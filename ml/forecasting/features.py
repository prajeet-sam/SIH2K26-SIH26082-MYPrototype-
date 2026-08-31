"""Feature-matrix construction for the forecasting engine.

Mirrors the causal constraints of `ml/features/builder.py`: only observations
with timestamp <= feature time may enter a feature row (no look-ahead leakage).
These builders operate over stored DB rows and are pollutant-generic so the
same machinery trains/serves PM2.5, PM10 and NO2 models.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta

import numpy as np

from ml.storage.models import PollutionObservation, WeatherObservation

FEATURE_SET_VERSION = "forecast-v1"

# Feature columns used by the ML model (must stay in a fixed order).
FEATURE_COLUMNS: tuple[str, ...] = (
    "target_lag1",
    "target_lag3",
    "target_lag6",
    "target_lag12",
    "target_lag24",
    "target_mean_6h",
    "target_mean_24h",
    "target_std_24h",
    "target_slope_3h",
    "temp_c",
    "rh_pct",
    "ws_ms",
    "wd_sin",
    "wd_cos",
    "precip_mm_6h",
    "pressure_hpa",
    "stagnation_24h",
    "rain_hours_24h",
    "hour_sin",
    "hour_cos",
    "month_sin",
    "month_cos",
)


def _hour_key(dt: datetime) -> datetime:
    return dt.replace(minute=0, second=0, microsecond=0)


def _hours(dt: datetime, ago: int) -> datetime:
    return _hour_key(dt) - timedelta(hours=ago)


def _grid_value(hourly: dict[datetime, float], feature_time: datetime, ago: int) -> float | None:
    return hourly.get(_hours(feature_time, ago))


def _series_by_hour(
    series: Sequence[tuple[datetime, float]], start: datetime, end: datetime
) -> dict[datetime, float]:
    """Snap (timestamp, value) pairs onto an hourly grid; later values win."""
    out: dict[datetime, float] = {}
    for ts, value in series:
        key = _hour_key(ts)
        if start <= ts <= end:
            out[key] = value
    return out


def build_pollution_series(
    rows: Sequence[PollutionObservation], pollutant: str
) -> list[tuple[datetime, float]]:
    return [
        (r.observed_at, float(r.value))
        for r in rows
        if r.pollutant == pollutant and r.value is not None and r.value >= 0
    ]


def build_weather_series(
    rows: Sequence[WeatherObservation],
) -> dict[datetime, WeatherObservation | None]:
    out: dict[datetime, WeatherObservation | None] = {}
    for r in rows:
        out[_hour_key(r.observed_at)] = r
    return out


def feature_row(
    feature_time: datetime,
    pollutant_series: Sequence[tuple[datetime, float]],
    weather_map: dict[datetime, WeatherObservation | None],
    lookback_hours: int = 24,
) -> dict[str, float]:
    """Build one feature dict for `feature_time` from series up to that time."""
    grid_start = feature_time - timedelta(hours=lookback_hours + 48)
    target = _series_by_hour(pollutant_series, grid_start, feature_time)

    def lag(ago: int) -> float | None:
        return target.get(_hours(feature_time, ago))

    l1, l3 = lag(1), lag(3)
    slope = (l1 - l3) / 2.0 if (l1 is not None and l3 is not None) else None

    vals6 = [
        target[_hours(feature_time, h)] for h in range(1, 7) if _hours(feature_time, h) in target
    ]
    vals24 = [
        target[_hours(feature_time, h)] for h in range(1, 25) if _hours(feature_time, h) in target
    ]
    mean6 = (sum(vals6) / len(vals6)) if vals6 else None
    mean24 = (sum(vals24) / len(vals24)) if vals24 else None
    std24 = float(np.std(vals24)) if len(vals24) >= 4 else None

    current_wx = None
    for ago in range(0, 3):
        w = weather_map.get(_hours(feature_time, ago))
        if w is not None:
            current_wx = w
            break

    rain6 = 0.0
    rain_hours24 = 0
    ws_values: list[float] = []
    for ago in range(0, 24):
        w = weather_map.get(_hours(feature_time, ago))
        if w is None:
            continue
        if ago < 6:
            rain6 += w.precipitation_mm or 0.0
        if (w.precipitation_mm or 0.0) > 0.1:
            rain_hours24 += 1
        if w.wind_speed_ms is not None:
            ws_values.append(w.wind_speed_ms)

    stagnation = (sum(1 for v in ws_values if v < 1.5) / len(ws_values)) if ws_values else None

    wd = current_wx.wind_direction_deg if current_wx else None

    row: dict[str, float] = {
        "target_lag1": lag(1),
        "target_lag3": lag(3),
        "target_lag6": lag(6),
        "target_lag12": lag(12),
        "target_lag24": lag(24),
        "target_mean_6h": mean6,
        "target_mean_24h": mean24,
        "target_std_24h": std24,
        "target_slope_3h": slope,
        "temp_c": current_wx.temperature_c if current_wx else None,
        "rh_pct": current_wx.relative_humidity_pct if current_wx else None,
        "ws_ms": current_wx.wind_speed_ms if current_wx else None,
        "wd_sin": (float(np.sin(np.radians(wd))) if wd is not None else None),
        "wd_cos": (float(np.cos(np.radians(wd))) if wd is not None else None),
        "precip_mm_6h": rain6,
        "pressure_hpa": current_wx.pressure_hpa if current_wx else None,
        "stagnation_24h": stagnation,
        "rain_hours_24h": float(rain_hours24),
        "hour_sin": float(np.sin(2 * np.pi * feature_time.hour / 24)),
        "hour_cos": float(np.cos(2 * np.pi * feature_time.hour / 24)),
        "month_sin": float(np.sin(2 * np.pi * feature_time.month / 12)),
        "month_cos": float(np.cos(2 * np.pi * feature_time.month / 12)),
    }
    # Only keep columns the model expects; drop None for rows where target present.
    return {k: row[k] for k in FEATURE_COLUMNS if k in row}


def feature_matrix(
    feature_times: Sequence[datetime],
    pollutant_series: Sequence[tuple[datetime, float]],
    weather_map: dict[datetime, WeatherObservation | None],
    lookback_hours: int = 24,
) -> list[dict[str, float]]:
    return [feature_row(t, pollutant_series, weather_map, lookback_hours) for t in feature_times]
