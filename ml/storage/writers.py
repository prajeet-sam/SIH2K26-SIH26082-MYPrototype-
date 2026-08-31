"""Persistence helpers: provider records -> observation tables (idempotent)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from ml.preprocessing.cleaning import CleaningReport
from ml.providers.base import PollutionRecord, WeatherRecord
from ml.storage.models import DataQualityLog, DataSource, PollutionObservation, WeatherObservation
from ml.storage.upsert import upsert_rows

POL_CONFLICT = ["station_slug", "pollutant", "observed_at", "source_id"]
WX_CONFLICT = ["station_slug", "observed_at", "source_id"]


def source_id_map(session: Session) -> dict[str, int]:
    return {row.provider_code: row.id for row in session.query(DataSource).all()}


def write_pollution(
    session: Session, records: list[PollutionRecord], report: CleaningReport
) -> tuple[int, int]:
    if not records:
        return (0, 0)
    ids = source_id_map(session)
    rows = []
    for r in records:
        sid = ids.get(r.source_code)
        if sid is None:
            continue
        rows.append(
            {
                "station_slug": r.station_slug,
                "pollutant": r.pollutant,
                "value": r.value,
                "unit": r.unit,
                "observed_at": r.observed_at.replace(tzinfo=None),
                "source_id": sid,
                "quality_flag": r.quality_flag,
            }
        )
    ins, upd = upsert_rows(
        session, PollutionObservation, rows, POL_CONFLICT, ["value", "unit", "quality_flag"]
    )
    for note in report.notes[:200]:
        session.add(
            DataQualityLog(
                station_slug=None,
                check_type="cleaning_drop",
                severity="warning",
                detail=note,
            )
        )
    session.commit()
    return (ins, upd)


def write_weather(session: Session, records: list[WeatherRecord]) -> tuple[int, int]:
    if not records:
        return (0, 0)
    ids = source_id_map(session)
    rows = []
    for r in records:
        sid = ids.get(r.source_code)
        if sid is None:
            continue
        rows.append(
            {
                "station_slug": r.station_slug,
                "observed_at": r.observed_at.replace(tzinfo=None),
                "temperature_c": r.temperature_c,
                "relative_humidity_pct": r.relative_humidity_pct,
                "wind_speed_ms": r.wind_speed_ms,
                "wind_direction_deg": r.wind_direction_deg,
                "wind_gust_ms": r.wind_gust_ms,
                "precipitation_mm": r.precipitation_mm,
                "pressure_hpa": r.pressure_hpa,
                "source_id": sid,
                "quality_flag": r.quality_flag,
            }
        )
    ins, upd = upsert_rows(
        session,
        WeatherObservation,
        rows,
        WX_CONFLICT,
        [
            "temperature_c",
            "relative_humidity_pct",
            "wind_speed_ms",
            "wind_direction_deg",
            "wind_gust_ms",
            "precipitation_mm",
            "pressure_hpa",
            "quality_flag",
        ],
    )
    session.commit()
    return (ins, upd)
