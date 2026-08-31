from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas import WeatherPointResponse
from ml.storage.models import WeatherObservation

router = APIRouter(prefix="/api/weather", tags=["weather"])


@router.get("/history", response_model=list[WeatherPointResponse])
def weather_history(
    station_id: str = Query(..., alias="station_id"),
    tail_hours: int = Query(72, alias="tail_hours", ge=1, le=720),
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=tail_hours)
    rows = (
        db.query(WeatherObservation)
        .filter(
            WeatherObservation.station_slug == station_id,
            WeatherObservation.observed_at >= cutoff,
        )
        .order_by(WeatherObservation.observed_at)
        .all()
    )
    seen: dict[str, WeatherObservation] = {}
    for r in rows:
        key = r.observed_at.strftime("%Y-%m-%dT%H:00:00")
        seen[key] = r
    return [
        WeatherPointResponse(
            time=key,
            temperature_c=r.temperature_c,
            relative_humidity_pct=r.relative_humidity_pct,
            wind_speed_ms=r.wind_speed_ms,
            wind_direction_deg=r.wind_direction_deg,
            precipitation_mm=r.precipitation_mm,
            pressure_hpa=r.pressure_hpa,
        )
        for key, r in sorted(seen.items())
    ]
