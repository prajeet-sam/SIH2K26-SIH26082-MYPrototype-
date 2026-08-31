"""Causal feature engineering for PM2.5 forecasting.

Hard constraints (see docs/research/scientific-methodology.md):
- Only data with timestamp <= feature_time may enter a feature row (no leakage).
- Future weather is allowed only through explicit forecast columns, never mixed
  into "observed" covariates.
- Every row records feature_set_version + dataset_hash for reproducibility.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import datetime

import numpy as np

from ml.storage.models import WeatherObservation

FEATURE_SET_VERSION = "fs-v1"

LAGS_H = (1, 3, 6, 12, 24)
ROLL_WINDOWS_H = (6, 24)


@dataclass(frozen=True)
class FeatureVector:
    station_slug: str
    feature_time: datetime

    pm25_lag1: float | None = None
    pm25_lag3: float | None = None
    pm25_lag6: float | None = None
    pm25_lag12: float | None = None
    pm25_lag24: float | None = None
    pm25_mean_6h: float | None = None
    pm25_mean_24h: float | None = None
    pm25_std_24h: float | None = None
    pm25_slope_3h: float | None = None

    temp_c: float | None = None
    rh_pct: float | None = None
    ws_ms: float | None = None
    wd_sin: float | None = None
    wd_cos: float | None = None
    precip_mm_6h: float | None = None
    pressure_hpa: float | None = None

    stagnation_24h: float | None = None
    rain_hours_24h: int = 0

    hour_sin: float = 0.0
    hour_cos: float = 0.0
    month_sin: float = 0.0
    month_cos: float = 0.0

    def to_payload(self) -> str:
        return json.dumps(asdict(self), default=str, sort_keys=True)


def dataset_hash(rows: Sequence[object]) -> str:
    h = hashlib.sha256()
    for r in rows:
        h.update(
            repr(sorted((k, v) for k, v in vars(r).items() if k != "_sa_instance_state")).encode()
        )
    return h.hexdigest()[:64]


def _series_by_hour(
    series: Sequence[tuple[datetime, float]], start: datetime, end: datetime
) -> dict[datetime, float]:
    """Snap (timestamp, value) pairs onto the hourly grid; later values win."""
    out: dict[datetime, float] = {}
    for ts, value in series:
        key = ts.replace(minute=0, second=0, microsecond=0)
        if start <= ts <= end:
            out[key] = value
    return out


def build_feature_vector(
    station_slug: str,
    feature_time: datetime,
    pm25_series: Sequence[tuple[datetime, float]],
    weather_series: Sequence[WeatherObservation],
) -> FeatureVector:
    grid_start = _hours(feature_time, 48)
    pm = _series_by_hour(pm25_series, grid_start, feature_time)

    def lag(h: int) -> float | None:
        return pm.get(_hours(feature_time, h))

    mean6 = _rolling(pm, feature_time, ROLL_WINDOWS_H[0])
    vals24 = [
        pm[_hours(feature_time, h)]
        for h in range(1, ROLL_WINDOWS_H[1] + 1)
        if _hours(feature_time, h) in pm
    ]
    mean24 = sum(vals24) / len(vals24) if vals24 else None
    std24 = float(np.std(vals24)) if len(vals24) >= 4 else None

    l1, l3 = lag(1), lag(3)
    slope = (l1 - l3) / 2.0 if (l1 is not None and l3 is not None) else None

    wx_by_hour = {
        w.observed_at.replace(minute=0, second=0, microsecond=0): w for w in weather_series
    }
    current_wx = None
    for h in range(0, 3):
        candidate = wx_by_hour.get(_hours(feature_time, h))
        if candidate is not None:
            current_wx = candidate
            break

    rain6 = 0.0
    rain_hours24 = 0
    ws_values_24: list[float] = []
    for h in range(0, 24):
        w = wx_by_hour.get(_hours(feature_time, h))
        if w is None:
            continue
        if h < 6:
            rain6 += w.precipitation_mm or 0.0
        if (w.precipitation_mm or 0.0) > 0.1:
            rain_hours24 += 1
        if h < 24 and w.wind_speed_ms is not None:
            ws_values_24.append(w.wind_speed_ms)

    stagnation = (
        (sum(1 for v in ws_values_24 if v < 1.5) / len(ws_values_24)) if ws_values_24 else None
    )

    wd = current_wx.wind_direction_deg if current_wx else None
    return FeatureVector(
        station_slug=station_slug,
        feature_time=feature_time,
        pm25_lag1=l1,
        pm25_lag3=lag(3),
        pm25_lag6=lag(6),
        pm25_lag12=lag(12),
        pm25_lag24=lag(24),
        pm25_mean_6h=mean6,
        pm25_mean_24h=mean24,
        pm25_std_24h=std24,
        pm25_slope_3h=slope,
        temp_c=current_wx.temperature_c if current_wx else None,
        rh_pct=current_wx.relative_humidity_pct if current_wx else None,
        ws_ms=current_wx.wind_speed_ms if current_wx else None,
        wd_sin=float(np.sin(np.radians(wd))) if wd is not None else None,
        wd_cos=float(np.cos(np.radians(wd))) if wd is not None else None,
        precip_mm_6h=rain6,
        pressure_hpa=current_wx.pressure_hpa if current_wx else None,
        stagnation_24h=stagnation,
        rain_hours_24h=rain_hours24,
        hour_sin=float(np.sin(2 * np.pi * feature_time.hour / 24)),
        hour_cos=float(np.cos(2 * np.pi * feature_time.hour / 24)),
        month_sin=float(np.sin(2 * np.pi * feature_time.month / 12)),
        month_cos=float(np.cos(2 * np.pi * feature_time.month / 12)),
    )


def _hours(t: datetime, ago: int) -> datetime:
    from datetime import timedelta

    return t.replace(minute=0, second=0, microsecond=0) - timedelta(hours=ago)


def _rolling(hourly: dict[datetime, float], feature_time: datetime, window_h: int) -> float | None:
    vals = [
        hourly[_hours(feature_time, h)]
        for h in range(1, window_h + 1)
        if _hours(feature_time, h) in hourly
    ]
    return sum(vals) / len(vals) if len(vals) >= max(2, window_h // 2) else None
