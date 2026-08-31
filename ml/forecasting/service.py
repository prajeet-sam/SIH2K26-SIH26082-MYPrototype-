"""Forecast service: turn stored observations into persisted, honest forecasts.

Serving priority:
1. If a trained ML model artifact is registered for (station, target), use it.
2. Otherwise use the transparent `PersistenceBaseline`, which is labelled as
   such so callers/UI never mistake it for a fitted ML model.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import desc
from sqlalchemy.orm import Session

from ml.forecasting import features as feat
from ml.forecasting.models import (
    ForecastPoint,
    ForecastResult,
    PersistenceBaseline,
    RidgeQuantileForecaster,
)
from ml.forecasting.weather import WeatherForecastRecord, fetch_weather_forecast
from ml.storage.models import Forecast, ModelRun, PollutionObservation, Station, WeatherObservation

MODEL_ARTIFACT_DIR = ".model-artifacts"


def utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


@dataclass
class LoadedContext:
    station: Station
    pollution: list[PollutionObservation]
    weather: dict[datetime, WeatherObservation | None]
    weather_forecast: list[WeatherForecastRecord] | None


def load_context(db: Session, slug: str, lookback_hours: int = 96) -> LoadedContext | None:
    station = db.query(Station).filter(Station.canonical_slug == slug).first()
    if station is None:
        return None
    cutoff = utcnow_naive() - timedelta(hours=lookback_hours + 48)
    pollution = (
        db.query(PollutionObservation)
        .filter(
            PollutionObservation.station_slug == slug,
            PollutionObservation.observed_at >= cutoff,
            PollutionObservation.value >= 0,
        )
        .order_by(PollutionObservation.observed_at)
        .all()
    )
    weather_rows = (
        db.query(WeatherObservation)
        .filter(
            WeatherObservation.station_slug == slug,
            WeatherObservation.observed_at >= cutoff,
        )
        .all()
    )
    weather_map = feat.build_weather_series(weather_rows)
    return LoadedContext(
        station=station, pollution=pollution, weather=weather_map, weather_forecast=None
    )


def latest_model_artifact(db: Session, slug: str, target: str) -> ModelRun | None:
    """Most recently deployed trained model for a specific (station, target).

    Station/target provenance lives on `model_metrics` (a ModelRun covers its
    metric rows): we select the newest `deployed` run that actually owns a
    metric row for this station+target, so stations never share artifacts.
    """
    from ml.storage.models import ModelMetric

    return (
        db.query(ModelRun)
        .join(ModelMetric, ModelMetric.model_run_id == ModelRun.id)
        .filter(
            ModelMetric.station_slug == slug,
            ModelMetric.target == target,
            ModelRun.status == "deployed",
        )
        .order_by(desc(ModelRun.trained_at))
        .first()
    )


def _load_ml_model(run: ModelRun) -> RidgeQuantileForecaster | None:
    if not run or not run.artifact_uri:
        return None
    import os

    artifact_path = os.path.join(MODEL_ARTIFACT_DIR, run.artifact_uri)
    if not os.path.exists(artifact_path):
        return None
    try:
        import joblib

        model = joblib.load(artifact_path)
        if isinstance(model, RidgeQuantileForecaster) and getattr(model, "_fitted", False):
            return model
    except Exception:  # noqa: BLE001 - corrupted artifact falls back to baseline
        return None
    return None


def _target_series(ctx: LoadedContext, target: str) -> list[tuple[datetime, float]]:
    # "aqi" is a derived composite target: overall CPCB AQI per hour, using the
    # max sub-index across whatever pollutants are observed at that hour. This
    # keeps the composite consistent with the per-pollutant AQI used by the UI.
    if target == "aqi":
        return _derived_aqi_series(ctx.pollution)
    return feat.build_pollution_series(ctx.pollution, target)


def _derived_aqi_series(
    rows: Sequence[PollutionObservation],
) -> list[tuple[datetime, float]]:
    from ml.preprocessing.aqi import overall_aqi

    hourly: dict[datetime, dict[str, float]] = {}
    for r in rows:
        if r.value is None or r.value < 0:
            continue
        key = _hour_key(r.observed_at)
        hourly.setdefault(key, {})[r.pollutant] = float(r.value)
    out: list[tuple[datetime, float]] = []
    for key, concentrations in hourly.items():
        aqi, _dominant = overall_aqi(concentrations)
        if aqi is not None:
            out.append((key, float(aqi)))
    out.sort(key=lambda kv: kv[0])
    return out


def _observed_tail(
    ctx: LoadedContext, target: str, tail_h: int = 8
) -> list[tuple[datetime, float]]:
    series = _target_series(ctx, target)
    return series[-tail_h:] if series else []


def _completed_weather_map(
    ctx: LoadedContext, horizon_times: list[datetime]
) -> dict[datetime, WeatherObservation | None]:
    """Observed weather map merged with forecast weather for horizon times."""
    merged: dict[datetime, WeatherObservation | None] = dict(ctx.weather)
    if ctx.weather_forecast:
        for rec in ctx.weather_forecast:
            if rec.observed_at in {
                t.replace(minute=0, second=0, microsecond=0) for t in horizon_times
            }:
                merged[rec.observed_at] = rec  # duck-typed, same attribute shape
    return merged


def _hour_key(dt: datetime) -> datetime:
    return dt.replace(minute=0, second=0, microsecond=0)


def generate_forecast(
    db: Session,
    station: Station,
    target: str,
    horizons: int = 48,
    ahead_hours: int = 72,
    fetch_weather: bool = True,
) -> ForecastResult:
    now = utcnow_naive()
    ctx = load_context(db, station.canonical_slug)
    if ctx is None:
        raise ValueError(f"unknown station: {station.canonical_slug}")

    series = _target_series(ctx, target)
    if not series:
        raise ValueError(
            f"no stored observations for {station.canonical_slug}/{target}; run ingestion first"
        )

    if fetch_weather:
        try:
            ctx.weather_forecast = fetch_weather_forecast(
                station.latitude, station.longitude, ahead_hours=ahead_hours
            )
        except Exception:  # noqa: BLE001 - weather forecast optional
            ctx.weather_forecast = None

    horizon_times = [_hour_key(now) + timedelta(hours=h) for h in range(1, horizons + 1)]
    weather_map = _completed_weather_map(ctx, horizon_times)

    # ML model if a deployed artifact exists.
    run = latest_model_artifact(db, station.canonical_slug, target)
    ml_model = _load_ml_model(run) if run else None

    if ml_model is not None:
        # Recursive multi-step: predict one horizon, feed p50 back as lag source.
        pseudo: dict[datetime, float] = {}
        points: list[ForecastPoint] = []
        try:
            for i, t in enumerate(horizon_times):
                hour = _hour_key(t)
                combined = list(series) + [(k, v) for k, v in pseudo.items()]
                row = feat.feature_row(hour, combined, weather_map)
                (p10, p50, p90) = ml_model.predict([row])[0]
                points.append(
                    ForecastPoint(target_time=t, horizon_hours=i + 1, p10=p10, p50=p50, p90=p90)
                )
                pseudo[hour] = p50
            return ForecastResult(
                points=points,
                issued_at=now,
                model_name=ml_model.name,
                model_version=ml_model.version,
                feature_set_version=feat.FEATURE_SET_VERSION,
                trained=True,
                model_run_id=run.id if run else None,
            )
        except Exception:  # noqa: BLE001 - native ML unavailable -> baseline
            pass

    # Fallback: persistence baseline on real observed data.
    recent_values = [v for _, v in series[-12:]]
    baseline = PersistenceBaseline(series[-1][1], recent_values)
    points = baseline.predict(horizon_times)
    return ForecastResult(
        points=points,
        issued_at=now,
        model_name=baseline.name,
        model_version=baseline.version,
        feature_set_version=feat.FEATURE_SET_VERSION,
        trained=False,
    )


def persist_forecast(
    db: Session,
    station_slug: str,
    target: str,
    result: ForecastResult,
    model_run_id: int | None = None,
) -> None:
    """Upsert forecast rows; remove superseded rows so only the latest issue remains."""
    if model_run_id is None:
        model_run_id = result.model_run_id
    # Remove any older issues for this station/target (bounded storage, UI reads latest).
    db.query(Forecast).filter(
        Forecast.station_slug == station_slug,
        Forecast.target == target,
    ).delete()
    for p in result.points:
        db.add(
            Forecast(
                station_slug=station_slug,
                target=target,
                issued_at=result.issued_at,
                target_time=p.target_time,
                horizon_hours=p.horizon_hours,
                p10=p.p10,
                p50=p.p50,
                p90=p.p90,
                confidence=_confidence(result, p),
                model_run_id=model_run_id,
                feature_set_version=result.feature_set_version,
            )
        )
    db.commit()


def _confidence(result: ForecastResult, point: ForecastPoint) -> str:
    if not result.trained:
        return "low"
    span = point.p90 - point.p10
    p50 = point.p50
    if p50 <= 0:
        return "moderate"
    rel = span / p50
    if rel <= 0.5:
        return "high"
    if rel <= 1.0:
        return "moderate"
    return "low"


def confidence_for(result: ForecastResult) -> str:
    if not result.points:
        return "low"
    return _confidence(result, result.points[0])
