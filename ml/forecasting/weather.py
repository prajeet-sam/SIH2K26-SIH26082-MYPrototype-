"""Weather forecast retrieval for the forecasting engine (Open-Meteo, keyless).

Returns hourly forecast records with the same attribute shape used by the
feature builder, so forecast-time feature vectors can reference future weather
(the documented "explicit forecast columns" path allowed by the methodology).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx


@dataclass
class WeatherForecastRecord:
    observed_at: datetime
    temperature_c: float | None
    relative_humidity_pct: float | None
    wind_speed_ms: float | None
    wind_direction_deg: float | None
    precipitation_mm: float | None
    pressure_hpa: float | None


FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HOURLY_FIELDS = [
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
    "wind_direction_10m",
    "precipitation",
    "surface_pressure",
]


def utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


_CACHE: dict[tuple[float, float, int], tuple[datetime, float, list[WeatherForecastRecord]]] = {}
_CACHE_TTL_SECONDS = 300.0


def _cached(latitude: float, longitude: float, ahead_hours: int) -> list[WeatherForecastRecord] | None:
    key = (round(latitude, 4), round(longitude, 4), ahead_hours)
    item = _CACHE.get(key)
    if not item:
        return None
    fetched_at, _timeout, records = item
    if (utcnow_naive() - fetched_at).total_seconds() > _CACHE_TTL_SECONDS:
        _CACHE.pop(key, None)
        return None
    return records


def _cell(series: list, idx: int) -> float | None:
    if idx >= len(series):
        return None
    raw = series[idx]
    return float(raw) if raw is not None else None


def fetch_weather_forecast(
    latitude: float,
    longitude: float,
    ahead_hours: int = 72,
    timeout_seconds: float = 15.0,
) -> list[WeatherForecastRecord]:
    """Fetch an hourly weather forecast for a point location (TTL-cached)."""
    ahead_hours = max(1, min(168, ahead_hours))

    cached = _cached(latitude, longitude, ahead_hours)
    if cached is not None:
        return cached

    params: dict[str, Any] = {
        "latitude": f"{latitude:.4f}",
        "longitude": f"{longitude:.4f}",
        "hourly": ",".join(HOURLY_FIELDS),
        "timezone": "UTC",
        "forecast_days": min(7, (ahead_hours + 23) // 24),
    }
    with httpx.Client(timeout=timeout_seconds) as client:
        resp = client.get(FORECAST_URL, params=params)
        resp.raise_for_status()
        payload = resp.json()

    hourly = payload.get("hourly", {})
    times = hourly.get("time", [])
    columns = {f: hourly.get(f, []) for f in HOURLY_FIELDS}
    now = utcnow_naive()

    records: list[WeatherForecastRecord] = []
    for i, ts in enumerate(times[:ahead_hours]):
        target_time = datetime.strptime(ts, "%Y-%m-%dT%H:%M")
        records.append(
            WeatherForecastRecord(
                observed_at=target_time,
                temperature_c=_cell(columns.get("temperature_2m", []), i),
                relative_humidity_pct=_cell(columns.get("relative_humidity_2m", []), i),
                wind_speed_ms=_cell(columns.get("wind_speed_10m", []), i),
                wind_direction_deg=_cell(columns.get("wind_direction_10m", []), i),
                precipitation_mm=_cell(columns.get("precipitation", []), i),
                pressure_hpa=_cell(columns.get("surface_pressure", []), i),
            )
        )
    result = [r for r in records if r.observed_at >= now - timedelta(minutes=90)]
    _CACHE[(round(latitude, 4), round(longitude, 4), ahead_hours)] = (
        now,
        timeout_seconds,
        result,
    )
    return result
