from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


def _camel(name: str) -> str:
    first, *rest = name.split("_")
    return first + "".join(w.capitalize() for w in rest)


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=_camel, populate_by_name=True)


# ── stations ────────────────────────────────────────────────────────────────


class StationResponse(CamelModel):
    id: str
    slug: str
    name: str
    city: str
    latitude: float
    longitude: float
    pollutants_available: list[str] = Field(default_factory=list)
    is_active: bool = True


# ── current conditions ─────────────────────────────────────────────────────


class WeatherNested(CamelModel):
    temperature_c: float | None = None
    relative_humidity_pct: float | None = None
    wind_speed_ms: float | None = None
    wind_direction_deg: float | None = None
    precipitation_mm: float | None = None


class CurrentConditionsResponse(CamelModel):
    station_id: str
    slug: str
    name: str
    city: str
    latitude: float
    longitude: float
    observed_at: str
    aqi: int
    category: str
    dominant_pollutant: str
    pollutants: dict[str, float] = Field(default_factory=dict)
    weather: WeatherNested = Field(default_factory=WeatherNested)
    freshness_minutes: float = 0
    trend_24h_aqi: list[int] = Field(default_factory=list)


# ── history ─────────────────────────────────────────────────────────────────


class ObservationPointResponse(CamelModel):
    time: str
    aqi: int | None = None
    pollutants: dict[str, float] = Field(default_factory=dict)
    quality_flag: str = "cleaned"


class WeatherPointResponse(CamelModel):
    time: str
    temperature_c: float | None = None
    relative_humidity_pct: float | None = None
    wind_speed_ms: float | None = None
    wind_direction_deg: float | None = None
    precipitation_mm: float | None = None
    pressure_hpa: float | None = None


# ── forecast ────────────────────────────────────────────────────────────────


class ForecastPointResponse(CamelModel):
    target_time: str
    horizon_hours: int
    p10: float | None = None
    p50: float | None = None
    p90: float | None = None
    confidence: str = "low"


class ForecastResponse(CamelModel):
    station_id: str
    station_name: str
    target: str
    issued_at: str
    model_run_id: str
    feature_set_version: str
    observed_tail: list[ObservationPointResponse] = Field(default_factory=list)
    weather_tail: list[WeatherPointResponse] = Field(default_factory=list)
    weather_forecast: list[WeatherPointResponse] = Field(default_factory=list)
    points: list[ForecastPointResponse] = Field(default_factory=list)


# ── explanation ─────────────────────────────────────────────────────────────


class ExplanationContribution(CamelModel):
    feature_label: str
    direction: Literal["up", "down"]
    weight_pct: float
    phrase: str


class ExplanationResponse(CamelModel):
    station_id: str
    station_name: str
    target: str
    generated_at: str
    narrative: str
    disclaimer: str
    confidence: str
    contributions: list[ExplanationContribution] = Field(default_factory=list)


# ── model performance ──────────────────────────────────────────────────────


class ModelMetricRowResponse(CamelModel):
    model_name: str
    target: str
    horizon_hours: int
    mae: float
    rmse: float
    mape: float
    r2: float
    skill_vs_persistence: float
    picp80: float | None = None
    pinaw80: float | None = None
    model_run_id: str


class GlobalImportanceItem(CamelModel):
    feature_label: str
    importance_pct: float
    family: str


# ── alerts ──────────────────────────────────────────────────────────────────


class AlertRuleResponse(CamelModel):
    id: str
    name: str
    metric: str
    comparator: str
    threshold: float
    window_hours: int | None = None
    horizon_filter: str | None = None
    enabled: bool = True
    cooldown_minutes: int = 60


class AlertRuleCreate(CamelModel):
    name: str
    metric: str
    comparator: str
    threshold: float
    window_hours: int | None = None
    horizon_filter: str | None = None
    enabled: bool = True
    cooldown_minutes: int = 60


class AlertRuleUpdate(CamelModel):
    name: str | None = None
    metric: str | None = None
    comparator: str | None = None
    threshold: float | None = None
    window_hours: int | None = None
    horizon_filter: str | None = None
    enabled: bool | None = None
    cooldown_minutes: int | None = None


class AlertContributor(CamelModel):
    label: str
    direction: Literal["up", "down"]


class AlertContext(CamelModel):
    value: float | None = None
    threshold: float | None = None
    horizon_hours: int | None = None
    contributors: list[AlertContributor] = Field(default_factory=list)


class AlertItemResponse(CamelModel):
    id: str
    alert_type: str
    severity: str
    station_slug: str | None = None
    station_name: str | None = None
    city: str | None = None
    triggered_at: str
    observed_or_forecast: str = "observed"
    message: str
    context: AlertContext = Field(default_factory=AlertContext)
    resolved_at: str | None = None


# ── data quality ────────────────────────────────────────────────────────────


class DataQualityIncidentResponse(CamelModel):
    id: str
    station_slug: str | None = None
    check_type: str
    severity: str
    detected_at: str
    resolved_at: str | None = None
    detail: str = ""


# ── station availability ───────────────────────────────────────────────────


class StationAvailabilityCell(CamelModel):
    day_iso: str
    pct_available: float


class StationAvailabilityResponse(CamelModel):
    slug: str
    matrix: dict[str, list[StationAvailabilityCell]] = Field(default_factory=dict)


# ── correlation matrix ─────────────────────────────────────────────────────


class CorrelationMatrixResponse(CamelModel):
    rows: list[str] = Field(default_factory=list)
    cols: list[str] = Field(default_factory=list)
    values: list[list[float]] = Field(default_factory=list)
