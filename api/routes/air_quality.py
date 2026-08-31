from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas import (
    CurrentConditionsResponse,
    ObservationPointResponse,
    WeatherNested,
)
from ml.preprocessing.aqi import categorize, overall_aqi
from ml.storage.models import PollutionObservation, Station, WeatherObservation

router = APIRouter(prefix="/api/air-quality", tags=["air-quality"])


def _aqi_at(series: dict[datetime, dict[str, float]], ts: datetime) -> int:
    aqi_val, _ = overall_aqi(series.get(ts, {}))
    return max(0, aqi_val) if aqi_val is not None else 0


@router.get("/current", response_model=list[CurrentConditionsResponse])
def current_conditions(db: Session = Depends(get_db)):
    """All-station conditions computed from three bulk queries, no N+1."""
    now = datetime.utcnow()
    stations = (
        db.query(Station).filter(Station.is_active.is_(True)).order_by(Station.canonical_slug).all()
    )
    slugs = {s.canonical_slug for s in stations}
    since = now - timedelta(hours=48)

    # 1) All pollutants for all stations in the 48h window (single query).
    pol_rows = (
        db.query(
            PollutionObservation.station_slug,
            PollutionObservation.pollutant,
            PollutionObservation.value,
            PollutionObservation.observed_at,
        )
        .filter(
            PollutionObservation.station_slug.in_(slugs),
            PollutionObservation.observed_at >= since,
        )
        .order_by(PollutionObservation.observed_at.asc())
        .all()
    )
    hourly: dict[str, dict[datetime, dict[str, float]]] = dict()
    latest: dict[str, dict[str, float]] = dict()
    for slug, pollutant, value, ts in pol_rows:
        bucket = hourly.setdefault(slug, defaultdict(dict))
        key = ts.replace(minute=0, second=0, microsecond=0)
        bucket[key][pollutant] = value
        latest.setdefault(slug, {})[pollutant] = value

    # 2) Latest weather for all stations (single query, windowed by freshness).
    wx_cutoff = now - timedelta(days=2)
    wx_rows = (
        db.query(WeatherObservation)
        .filter(
            WeatherObservation.station_slug.in_(slugs),
            WeatherObservation.observed_at >= wx_cutoff,
        )
        .order_by(WeatherObservation.observed_at.desc())
        .all()
    )
    wx_latest: dict[str, WeatherObservation] = {}
    for w in wx_rows:
        wx_latest.setdefault(w.station_slug, w)

    result: list[CurrentConditionsResponse] = []
    for s in stations:
        series = hourly.get(s.canonical_slug)
        pollutants = latest.get(s.canonical_slug)
        if not series or not pollutants:
            continue

        aqi_val, dominant = overall_aqi(pollutants)
        if aqi_val is None:
            aqi_val = 0
        cat = categorize(aqi_val)

        wx = wx_latest.get(s.canonical_slug)
        weather = WeatherNested()
        freshness = 999.0
        if wx:
            weather = WeatherNested(
                temperature_c=wx.temperature_c,
                relative_humidity_pct=wx.relative_humidity_pct,
                wind_speed_ms=wx.wind_speed_ms,
                wind_direction_deg=wx.wind_direction_deg,
                precipitation_mm=wx.precipitation_mm,
            )
            freshness = max(0, (now - wx.observed_at).total_seconds() / 60)

        trend = [
            _aqi_at(series, (now - timedelta(hours=h)).replace(minute=0, second=0, microsecond=0))
            for h in range(24, -1, -1)
        ]

        result.append(
            CurrentConditionsResponse(
                station_id=s.canonical_slug,
                slug=s.canonical_slug,
                name=s.name,
                city=s.city,
                latitude=s.latitude,
                longitude=s.longitude,
                observed_at=now.isoformat(),
                aqi=aqi_val,
                category=cat,
                dominant_pollutant=dominant or "pm25",
                pollutants=pollutants,
                weather=weather,
                freshness_minutes=round(freshness, 1),
                trend_24h_aqi=trend,
            )
        )
    return result


@router.get("/history", response_model=list[ObservationPointResponse])
def observation_history(
    station_id: str = Query(..., alias="station_id"),
    tail_hours: int = Query(72, alias="tail_hours", ge=1, le=720),
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=tail_hours)
    rows = (
        db.query(PollutionObservation)
        .filter(
            PollutionObservation.station_slug == station_id,
            PollutionObservation.observed_at >= cutoff,
        )
        .order_by(PollutionObservation.observed_at)
        .all()
    )

    by_hour: dict[str, dict[str, float]] = defaultdict(dict)
    flagged: dict[str, set[str]] = defaultdict(set)
    for r in rows:
        key = r.observed_at.strftime("%Y-%m-%dT%H:00:00")
        by_hour[key][r.pollutant] = r.value
        flagged[key].add(r.quality_flag)

    PRIORITY = {"suspect": 4, "interpolated": 3, "raw": 2, "cleaned": 1}

    result: list[ObservationPointResponse] = []
    for ts_str, pollutant_map in sorted(by_hour.items()):
        aqi_val, _ = overall_aqi(pollutant_map)
        flags = flagged[ts_str]
        quality = max(flags, key=lambda f: PRIORITY.get(f, 0), default="cleaned")
        result.append(
            ObservationPointResponse(
                time=ts_str,
                aqi=max(0, aqi_val) if aqi_val is not None else None,
                pollutants=pollutant_map,
                quality_flag=quality,
            )
        )
    return result
