from __future__ import annotations

from datetime import UTC, datetime, timedelta

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas import CorrelationMatrixResponse
from ml.storage.models import PollutionObservation, Station, WeatherObservation

router = APIRouter(prefix="/api/research", tags=["research"])

POLLUTANTS = ("pm25", "pm10", "no2", "so2", "o3", "co")
WEATHER = (
    ("temperature_c", "Temp"),
    ("relative_humidity_pct", "Humidity"),
    ("wind_speed_ms", "Wind"),
    ("precipitation_mm", "Rain"),
    ("pressure_hpa", "Pressure"),
)


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


@router.get("/correlations", response_model=CorrelationMatrixResponse)
def correlations(
    station_id: str = Query(..., alias="station_id"),
    days: int = Query(30, alias="days", ge=1, le=90),
    db: Session = Depends(get_db),
):
    station = db.query(Station).filter(Station.canonical_slug == station_id).first()
    if station is None:
        raise HTTPException(status_code=404, detail=f"unknown station: {station_id}")

    cutoff = _utcnow() - timedelta(days=days)
    pol = (
        db.query(PollutionObservation)
        .filter(
            PollutionObservation.station_slug == station_id,
            PollutionObservation.observed_at >= cutoff,
        )
        .all()
    )
    wx = (
        db.query(WeatherObservation)
        .filter(
            WeatherObservation.station_slug == station_id,
            WeatherObservation.observed_at >= cutoff,
        )
        .all()
    )

    if not pol:
        raise HTTPException(
            status_code=404,
            detail=f"no pollution data for {station_id} in the past {days} days",
        )

    # Pollutant hourly series.
    pol_by_hour: dict[str, dict[datetime, float]] = {p: {} for p in POLLUTANTS}
    for r in pol:
        key = r.observed_at.replace(minute=0, second=0, microsecond=0)
        if r.pollutant in pol_by_hour and r.value is not None:
            pol_by_hour[r.pollutant][key] = r.value

    # Weather hourly series.
    wx_by_hour: dict[str, dict[datetime, float]] = {label: {} for _, label in WEATHER}
    for r in wx:
        key = r.observed_at.replace(minute=0, second=0, microsecond=0)
        for attr, label in WEATHER:
            val = getattr(r, attr)
            if val is not None:
                wx_by_hour[label][key] = float(val)

    # Build rows keyed by hour, aligning pollutants vs weather.
    hour_sets = [set(v) for v in pol_by_hour.values()] + [set(v) for v in wx_by_hour.values()]
    all_hours = set.union(*hour_sets) if hour_sets else set()
    rows: list[dict[str, float]] = []
    for h in all_hours:
        row: dict[str, float] = {}
        for p in POLLUTANTS:
            row[p] = pol_by_hour[p].get(h)
        for label in wx_by_hour:
            row[label] = wx_by_hour[label].get(h)
        rows.append(row)

    # Variables to show: pollutants (cols) vs weather + pollutants (rows).
    cols = [p for p in POLLUTANTS if any(r.get(p) is not None for r in rows)]
    row_labels = [p for p in cols] + [label for _, label in WEATHER if label in wx_by_hour]
    col_labels = cols

    def pearson(a: list[float], b: list[float]) -> float:
        pairs = [(x, y) for x, y in zip(a, b, strict=False) if x is not None and y is not None]
        if len(pairs) < 3:
            return 0.0
        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]
        xm, ym = float(np.mean(xs)), float(np.mean(ys))
        num = sum((x - xm) * (y - ym) for x, y in pairs)
        denom = (sum((x - xm) ** 2 for x in xs) * sum((y - ym) ** 2 for y in ys)) ** 0.5
        return round(float(num / denom), 3) if denom > 0 else 0.0

    values: list[list[float]] = []
    for rlab in row_labels:
        rvec = [row.get(rlab) for row in rows]
        values.append([pearson(rvec, [row.get(clab) for row in rows]) for clab in col_labels])

    return CorrelationMatrixResponse(rows=row_labels, cols=col_labels, values=values)
