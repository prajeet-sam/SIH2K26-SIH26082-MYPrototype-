from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utcnow_naive, server_default=func.current_timestamp()
    )


POLLUTANTS = ("pm25", "pm10", "no2", "so2", "co", "o3", "nh3")
QUALITY_FLAGS = ("raw", "cleaned", "interpolated", "suspect")


class DataSource(Base, TimestampMixin):
    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(255))
    requires_key: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Station(Base, TimestampMixin):
    __tablename__ = "stations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical_slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    city: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    region: Mapped[str] = mapped_column(String(40), nullable=False, default="NCR")
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_json: Mapped[str | None] = mapped_column(Text)


class StationNameAlias(Base, TimestampMixin):
    __tablename__ = "station_name_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider_id: Mapped[int] = mapped_column(
        ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False
    )
    provider_name: Mapped[str] = mapped_column(String(200), nullable=False)
    canonical_slug: Mapped[str] = mapped_column(
        ForeignKey("stations.canonical_slug", ondelete="CASCADE"), nullable=False
    )

    __table_args__ = (UniqueConstraint("provider_id", "provider_name", name="uq_provider_alias"),)


class PollutionObservation(Base, TimestampMixin):
    __tablename__ = "pollution_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_slug: Mapped[str] = mapped_column(
        ForeignKey("stations.canonical_slug", ondelete="RESTRICT"), nullable=False
    )
    pollutant: Mapped[str] = mapped_column(String(8), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(16), nullable=False, default="ug/m3")
    observed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("data_sources.id", ondelete="RESTRICT"), nullable=False
    )
    quality_flag: Mapped[str] = mapped_column(String(16), nullable=False, default="cleaned")

    __table_args__ = (
        UniqueConstraint(
            "station_slug", "pollutant", "observed_at", "source_id", name="uq_pollution_obs"
        ),
        CheckConstraint("value >= 0", name="ck_pollution_nonnegative"),
        Index("ix_pol_station_time", "station_slug", "pollutant", "observed_at"),
    )


class WeatherObservation(Base, TimestampMixin):
    __tablename__ = "weather_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_slug: Mapped[str] = mapped_column(
        ForeignKey("stations.canonical_slug", ondelete="RESTRICT"), nullable=False
    )
    observed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    temperature_c: Mapped[float | None] = mapped_column(Float)
    relative_humidity_pct: Mapped[float | None] = mapped_column(Float)
    wind_speed_ms: Mapped[float | None] = mapped_column(Float)
    wind_direction_deg: Mapped[float | None] = mapped_column(Float)
    wind_gust_ms: Mapped[float | None] = mapped_column(Float)
    precipitation_mm: Mapped[float | None] = mapped_column(Float)
    pressure_hpa: Mapped[float | None] = mapped_column(Float)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("data_sources.id", ondelete="RESTRICT"), nullable=False
    )
    quality_flag: Mapped[str] = mapped_column(String(16), nullable=False, default="cleaned")

    __table_args__ = (
        UniqueConstraint("station_slug", "observed_at", "source_id", name="uq_weather_obs"),
        CheckConstraint(
            "relative_humidity_pct IS NULL OR (relative_humidity_pct BETWEEN 0 AND 100)",
            name="ck_rh_range",
        ),
        CheckConstraint("wind_speed_ms IS NULL OR wind_speed_ms >= 0", name="ck_ws_nonnegative"),
        CheckConstraint(
            "precipitation_mm IS NULL OR precipitation_mm >= 0", name="ck_precip_nonneg"
        ),
        Index("ix_wx_station_time", "station_slug", "observed_at"),
    )


class DataQualityLog(Base, TimestampMixin):
    __tablename__ = "data_quality_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_slug: Mapped[str | None] = mapped_column(String(80))
    check_type: Mapped[str] = mapped_column(String(48), nullable=False)
    severity: Mapped[str] = mapped_column(String(12), nullable=False, default="info")
    detail: Mapped[str | None] = mapped_column(Text)
    detected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow_naive)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
    source_id: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (Index("ix_dq_detected", "detected_at"),)


class FeatureRow(Base, TimestampMixin):
    __tablename__ = "features"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_slug: Mapped[str] = mapped_column(
        ForeignKey("stations.canonical_slug", ondelete="CASCADE"), nullable=False
    )
    feature_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    horizon_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    feature_set_version: Mapped[str] = mapped_column(String(48), nullable=False)
    dataset_hash: Mapped[str | None] = mapped_column(String(64))
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "station_slug",
            "feature_time",
            "horizon_hours",
            "feature_set_version",
            name="uq_feature_row",
        ),
        Index("ix_feat_station_time", "station_slug", "feature_set_version", "feature_time"),
    )


class ModelRun(Base, TimestampMixin):
    __tablename__ = "model_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(48))
    params_json: Mapped[str | None] = mapped_column(Text)
    train_start: Mapped[datetime | None] = mapped_column(DateTime)
    train_end: Mapped[datetime | None] = mapped_column(DateTime)
    val_scheme: Mapped[str | None] = mapped_column(String(48))
    dataset_hash: Mapped[str | None] = mapped_column(String(64))
    git_sha: Mapped[str | None] = mapped_column(String(48))
    random_seed: Mapped[int | None] = mapped_column(Integer)
    artifact_uri: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="training")
    trained_at: Mapped[datetime | None] = mapped_column(DateTime)


class Forecast(Base, TimestampMixin):
    __tablename__ = "forecasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_slug: Mapped[str] = mapped_column(
        ForeignKey("stations.canonical_slug", ondelete="CASCADE"), nullable=False
    )
    target: Mapped[str] = mapped_column(String(12), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    target_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    horizon_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    p50: Mapped[float | None] = mapped_column(Float)
    p10: Mapped[float | None] = mapped_column(Float)
    p90: Mapped[float | None] = mapped_column(Float)
    confidence: Mapped[str | None] = mapped_column(String(12))
    model_run_id: Mapped[int | None] = mapped_column(ForeignKey("model_runs.id"))
    feature_set_version: Mapped[str | None] = mapped_column(String(48))

    __table_args__ = (
        UniqueConstraint(
            "station_slug", "target", "issued_at", "horizon_hours", name="uq_forecast"
        ),
        Index("ix_fc_station_target_time", "station_slug", "target", "target_time"),
    )


class ModelMetric(Base, TimestampMixin):
    __tablename__ = "model_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_run_id: Mapped[int] = mapped_column(
        ForeignKey("model_runs.id", ondelete="CASCADE"), nullable=False
    )
    scope: Mapped[str] = mapped_column(String(16), nullable=False, default="overall")
    station_slug: Mapped[str | None] = mapped_column(String(80))
    season: Mapped[str | None] = mapped_column(String(16))
    target: Mapped[str] = mapped_column(String(12), nullable=False)
    horizon_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    mae: Mapped[float | None] = mapped_column(Float)
    rmse: Mapped[float | None] = mapped_column(Float)
    mape: Mapped[float | None] = mapped_column(Float)
    r2: Mapped[float | None] = mapped_column(Float)
    smape: Mapped[float | None] = mapped_column(Float)
    picp_80: Mapped[float | None] = mapped_column(Float)
    pinaw_80: Mapped[float | None] = mapped_column(Float)
    winkler_80: Mapped[float | None] = mapped_column(Float)
    extra_json: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (Index("ix_metric_lookup", "target", "horizon_hours", "scope"),)


class AlertRule(Base, TimestampMixin):
    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    metric: Mapped[str] = mapped_column(String(32), nullable=False)
    comparator: Mapped[str] = mapped_column(String(4), nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    window_hours: Mapped[int | None] = mapped_column(Integer)
    horizon_filter: Mapped[str | None] = mapped_column(String(64))
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    cooldown_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)


class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_type: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[str] = mapped_column(String(12), nullable=False, default="info")
    station_slug: Mapped[str | None] = mapped_column(String(80))
    triggered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow_naive)
    observed_or_forecast: Mapped[str] = mapped_column(
        String(12), nullable=False, default="observed"
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    context_json: Mapped[str | None] = mapped_column(Text)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)

    __table_args__ = (Index("ix_alert_triggered", "triggered_at"),)


class DatasetVersion(Base, TimestampMixin):
    __tablename__ = "dataset_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    row_counts_json: Mapped[str | None] = mapped_column(Text)
