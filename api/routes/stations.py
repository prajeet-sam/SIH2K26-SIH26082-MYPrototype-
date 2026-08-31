from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas import StationResponse
from ml.storage.models import PollutionObservation, Station

router = APIRouter(prefix="/api", tags=["stations"])


@router.get("/stations", response_model=list[StationResponse])
def list_stations(db: Session = Depends(get_db)):
    stations = (
        db.query(Station).filter(Station.is_active.is_(True)).order_by(Station.canonical_slug).all()
    )

    rows = (
        db.query(PollutionObservation.station_slug, PollutionObservation.pollutant).distinct().all()
    )
    available_pollutants: dict[str, list[str]] = {}
    for slug, pollutant in rows:
        available_pollutants.setdefault(slug, []).append(pollutant)

    return [
        StationResponse(
            id=s.canonical_slug,
            slug=s.canonical_slug,
            name=s.name,
            city=s.city,
            latitude=s.latitude,
            longitude=s.longitude,
            pollutants_available=available_pollutants.get(s.canonical_slug, []),
            is_active=s.is_active,
        )
        for s in stations
    ]
