from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas import StationAvailabilityCell, StationAvailabilityResponse
from ml.storage.models import PollutionObservation

router = APIRouter(prefix="/api/stations", tags=["stations"])


@router.get("/{slug}/availability", response_model=StationAvailabilityResponse)
def station_availability(
    slug: str,
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()
    days = 30
    start = now - timedelta(days=days)
    rows = (
        db.query(
            func.date(PollutionObservation.observed_at).label("day"),
            PollutionObservation.pollutant,
            func.count(PollutionObservation.id).label("cnt"),
        )
        .filter(
            PollutionObservation.station_slug == slug,
            PollutionObservation.observed_at >= start,
        )
        .group_by("day", PollutionObservation.pollutant)
        .all()
    )
    matrix: dict[str, list[StationAvailabilityCell]] = {}
    for day_str, pollutant, cnt in rows:
        matrix.setdefault(pollutant, []).append(
            StationAvailabilityCell(day_iso=str(day_str), pct_available=min(100.0, cnt / 24 * 100))
        )
    for pollutant in matrix:
        matrix[pollutant].sort(key=lambda c: c.day_iso)
    return StationAvailabilityResponse(slug=slug, matrix=matrix)
