from __future__ import annotations

from datetime import UTC, datetime, timedelta

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import get_db
from api.schemas import (
    ExplanationResponse,
    ForecastPointResponse,
    ForecastResponse,
    ObservationPointResponse,
    WeatherPointResponse,
)
from ml.forecasting.explain import explain_forecast
from ml.forecasting.service import generate_forecast, persist_forecast
from ml.forecasting.weather import fetch_weather_forecast
from ml.preprocessing.aqi import overall_aqi
from ml.storage.models import Forecast, PollutionObservation, Station
from sqlalchemy import desc

router = APIRouter(prefix="/api/forecast", tags=["forecast"])


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _station_or_404(db: Session, slug: str) -> Station:
    station = db.query(Station).filter(Station.canonical_slug == slug).first()
    if station is None:
        raise HTTPException(status_code=404, detail=f"unknown station: {slug}")
    return station


def _observed_tail(
    db: Session, station: Station, target: str, tail_h: int = 8
) -> list[ObservationPointResponse]:
    cutoff = _utcnow() - timedelta(hours=tail_h * 2 + 48)
    rows = (
        db.query(PollutionObservation)
        .filter(
            PollutionObservation.station_slug == station.canonical_slug,
            PollutionObservation.pollutant == target,
            PollutionObservation.observed_at >= cutoff,
        )
        .order_by(PollutionObservation.observed_at)
        .all()
    )
    # hourly buckets -> (time, last_value)
    buckets: dict[datetime, float] = {}
    for r in rows:
        key = r.observed_at.replace(minute=0, second=0, microsecond=0)
        buckets[key] = r.value
    out: list[ObservationPointResponse] = []
    for ts in sorted(buckets)[-tail_h:]:
        aqi, _ = overall_aqi({target: buckets[ts]})
        out.append(
            ObservationPointResponse(
                time=ts.isoformat(),
                aqi=aqi,
                pollutants={target: buckets[ts]},
                quality_flag="cleaned",
            )
        )
    return out


def _weather_forecast_points(station: Station, ahead_hours: int = 72) -> list[WeatherPointResponse]:
    try:
        records = fetch_weather_forecast(
            station.latitude, station.longitude, ahead_hours=ahead_hours
        )
    except Exception:  # noqa: BLE001 - optional
        return []
    return [
        WeatherPointResponse(
            time=r.observed_at.isoformat(),
            temperature_c=r.temperature_c,
            relative_humidity_pct=r.relative_humidity_pct,
            wind_speed_ms=r.wind_speed_ms,
            wind_direction_deg=r.wind_direction_deg,
            precipitation_mm=r.precipitation_mm,
            pressure_hpa=r.pressure_hpa,
        )
        for r in records
    ]


def _has_per_horizon_model(db: Session, slug: str, target: str, horizon: int) -> bool:
    from ml.storage.models import ModelRun
    result = (
        db.query(ModelRun)
        .filter(ModelRun.status == "deployed")
        .filter(ModelRun.horizon == horizon)  # type: ignore[attr-defined]
        .filter(
            ModelRun.id.in_(
                db.query(ModelMetric.model_run_id)
                .filter(ModelMetric.station_slug == slug, ModelMetric.target == target)
                .distinct()
            )
        )
        .first()
    )
    return result is not None


def _load_ml_model(run):
    if not run or not getattr(run, "artifact_uri", None):
        return None
    import os

    artifact_path = os.path.join(".model-artifacts", run.artifact_uri)
    if not os.path.exists(artifact_path):
        return None
    try:
        import joblib

        model = joblib.load(artifact_path)
        if getattr(model, "_fitted", False):
            return model
    except Exception:  # noqa: BLE001 - corrupted artifact falls back to baseline
        return None
    return None


@router.get("/weather", response_model=list[WeatherPointResponse])
def weather_forecast(
    station_id: str = Query(..., alias="station_id"),
    ahead_hours: int = Query(72, alias="ahead_hours", ge=1, le=168),
    db: Session = Depends(get_db),
):
    station = _station_or_404(db, station_id)
    return _weather_forecast_points(station, ahead_hours)


@router.get("/{slug}", response_model=ForecastResponse)
def get_forecast(
    slug: str,
    targets: str = Query("pm25", alias="targets"),
    horizons: int = Query(48, alias="horizons", ge=1, le=168),
    horizon: int = Query(1, alias="horizon", ge=1, le=168),
    db: Session = Depends(get_db),
):
    station = _station_or_404(db, slug)
    target = targets.split(",")[0]

    # Try per-horizon deployed model when horizon != 1.
    # For horizon=1 we keep the scheduler-issued forecast path for backward compatibility.
    use_per_horizon = horizon != 1 and _has_per_horizon_model(db, slug, target, horizon)

    result_model_run_id = ""
    feature_set_version = "forecast-v1"
    issue_time = _utcnow()

    points: list[ForecastPointResponse] = []

    if use_per_horizon:
        hr_model = latest_model_artifact(db, slug, target)
        if hr_model is not None:
            hr_model_loaded = _load_ml_model(hr_model)
            if hr_model_loaded is not None:
                try:
                    sh = hr_model.horizon
                    hr_result = generate_forecast(db, station, target, horizons=horizon, ahead_hours=sh)
                    issue_time = hr_result.issued_at
                    feature_set_version = hr_result.feature_set_version
                    result_model_run_id = str(hr_model.id) if hr_model.id else ""
                    points = [
                        ForecastPointResponse(
                            target_time=p.target_time.isoformat(),
                            horizon_hours=p.horizon_hours,
                            p10=p.p10,
                            p50=p.p50,
                            p90=p.p90,
                            confidence="low" if not hr_result.trained else "moderate",
                        )
                        for p in hr_result.points[:horizon]
                    ]
                except Exception:
                    pass  # fall back to persisted forecasts

    if not points:
        # Prefer persisted forecast rows emitted by the scheduler.
        latest = (
            db.query(Forecast.issued_at)
            .filter(Forecast.station_slug == slug, Forecast.target == target)
            .order_by(desc(Forecast.issued_at))
            .first()
        )

        rows = ()
        if latest is not None:
            rows = (
                db.query(Forecast)
                .filter(
                    Forecast.station_slug == slug,
                    Forecast.target == target,
                    Forecast.issued_at == latest[0],
                )
                .order_by(Forecast.horizon_hours)
                .limit(horizons)
                .all()
            )
        points = []
        if rows:
            result_model_run_id = str(rows[0].model_run_id) if rows[0].model_run_id else ""
            issue_time = latest[0]
            points = [
                ForecastPointResponse(
                    target_time=r.target_time.isoformat(),
                    horizon_hours=r.horizon_hours,
                    p10=r.p10,
                    p50=r.p50,
                    p90=r.p90,
                    confidence=r.confidence or "low",
                )
                for r in rows
            ]
        else:
            # No scheduled forecast yet: generate on demand and persist (labelled).
            try:
                result = generate_forecast(db, station, target, horizons=horizons)
                issue_time = result.issued_at
                feature_set_version = result.feature_set_version
                result_model_run_id = str(result.model_run_id) or ""
                points = [
                    ForecastPointResponse(
                        target_time=p.target_time.isoformat(),
                        horizon_hours=p.horizon_hours,
                        p10=p.p10,
                        p50=p.p50,
                        p90=p.p90,
                        confidence="low" if not result.trained else "moderate",
                    )
                    for p in result.points[:horizons]
                ]
                try:
                    persist_forecast(db, slug, target, result)
                except Exception:  # noqa: BLE001 - persisting best-effort
                    pass
            except ValueError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ForecastResponse(
        station_id=slug,
        station_name=station.name,
        target=target,
        issued_at=issue_time.isoformat(),
        model_run_id=result_model_run_id,
        feature_set_version=feature_set_version,
        observed_tail=_observed_tail(db, station, target),
        weather_forecast=_weather_forecast_points(station, ahead_hours=72),
        points=points,
    )