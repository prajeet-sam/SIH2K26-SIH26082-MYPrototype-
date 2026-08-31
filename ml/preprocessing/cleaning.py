"""Cleaning/validation chain for ingested records.

Every record passes through with a quality flag; violations are logged to
data_quality_logs and (depending on severity) dropped or flagged. Nothing is
silently mutated: drops are explicit and counted.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from ml.providers.base import PollutionRecord, WeatherRecord

POLLUTANT_LIMITS_UG: dict[str, float] = {
    "pm25": 2000.0,
    "pm10": 3000.0,
    "no2": 1000.0,
    "so2": 1000.0,
    "o3": 1500.0,
    "nh3": 2000.0,
}
# CO arrives in mg/m3
CO_LIMIT_MG = 50.0

MAX_FUTURE_SKEW = timedelta(minutes=90)
MAX_AGE = timedelta(days=95)


@dataclass
class CleaningReport:
    seen: int = 0
    kept: int = 0
    dropped_future: int = 0
    dropped_stale: int = 0
    dropped_range: int = 0
    flagged_suspect: int = 0
    notes: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"seen={self.seen} kept={self.kept} "
            f"dropped(future={self.dropped_future}, stale={self.dropped_stale}, range={self.dropped_range}) "
            f"flagged_suspect={self.flagged_suspect}"
        )


def _time_bounds(now_utc: datetime) -> tuple[datetime, datetime]:
    return now_utc - MAX_AGE, now_utc + MAX_FUTURE_SKEW


def clean_pollution(
    records: Sequence[PollutionRecord], now_utc: datetime | None = None
) -> tuple[list[PollutionRecord], CleaningReport]:
    now_utc = now_utc or datetime.utcnow()
    min_ts, max_ts = _time_bounds(now_utc)
    report = CleaningReport(seen=len(records))
    out: list[PollutionRecord] = []
    for r in records:
        if r.observed_at > max_ts:
            report.dropped_future += 1
            continue
        if r.observed_at < min_ts:
            report.dropped_stale += 1
            continue

        limit = CO_LIMIT_MG if r.pollutant == "co" else POLLUTANT_LIMITS_UG.get(r.pollutant)
        if r.value < 0 or (limit is not None and r.value > limit):
            report.dropped_range += 1
            report.notes.append(
                f"drop {r.station_slug}/{r.pollutant}@{r.observed_at.isoformat()} value={r.value}"
            )
            continue

        record = r.model_copy()
        # Model-derived feeds are labelled interpolated; sensor feeds keep their raw flag.
        if record.source_code.startswith("open-meteo") and record.quality_flag == "cleaned":
            record.quality_flag = "interpolated"
        if record.value > 0.8 * (limit or 1e9):
            record.quality_flag = "suspect"
            report.flagged_suspect += 1
        out.append(record)

    report.kept = len(out)
    return out, report


def clean_weather(
    records: Sequence[WeatherRecord], now_utc: datetime | None = None
) -> tuple[list[WeatherRecord], CleaningReport]:
    now_utc = now_utc or datetime.utcnow()
    min_ts, max_ts = _time_bounds(now_utc)
    report = CleaningReport(seen=len(records))
    out: list[WeatherRecord] = []
    for r in records:
        if r.observed_at > max_ts:
            report.dropped_future += 1
            continue
        if r.observed_at < min_ts:
            report.dropped_stale += 1
            continue

        bad_range = (
            (r.relative_humidity_pct is not None and not (0 <= r.relative_humidity_pct <= 100))
            or (r.wind_speed_ms is not None and r.wind_speed_ms > 60)
            or (r.precipitation_mm is not None and r.precipitation_mm < 0)
            or (r.temperature_c is not None and not (-20 <= r.temperature_c <= 60))
        )
        if bad_range:
            report.dropped_range += 1
            report.notes.append(f"drop weather {r.station_slug}@{r.observed_at.isoformat()}")
            continue
        out.append(r.model_copy())

    report.kept = len(out)
    return out, report
