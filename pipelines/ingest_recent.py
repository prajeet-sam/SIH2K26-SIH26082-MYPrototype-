"""Ingest recent observations from the best available providers into storage.

Usage:
    python -m pipelines.ingest_recent --hours 48
    python -m pipelines.ingest_recent --start 2026-01-01T00:00Z --end 2026-01-05T00:00Z
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta

from ml.config.settings import get_settings
from ml.preprocessing.cleaning import CleaningReport, clean_pollution, clean_weather
from ml.providers.base import PollutionRecord, StationRef, WeatherRecord
from ml.providers.registry import build_air_quality_providers, build_weather_providers
from ml.storage.db import init_schema, make_engine, make_session_factory
from ml.storage.models import Station
from ml.storage.writers import write_pollution, write_weather


def utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def parse_utc(text: str) -> datetime:
    dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if dt.tzinfo is not None:
        return dt.astimezone(UTC).replace(tzinfo=None)
    return dt


def load_station_refs(factory) -> list[StationRef]:
    with factory() as session:
        rows = session.query(Station).filter(Station.is_active.is_(True)).all()
        return [
            StationRef(
                slug=s.canonical_slug,
                name=s.name,
                city=s.city,
                latitude=s.latitude,
                longitude=s.longitude,
            )
            for s in rows
        ]


def run(window_start: datetime, window_end: datetime) -> dict[str, str]:
    settings = get_settings()
    engine = make_engine(settings)
    init_schema(engine)
    factory = make_session_factory(engine)

    refs = load_station_refs(factory)
    now = utcnow_naive()
    hard_end = min(window_end, now)
    results: dict[str, str] = {}

    pol_records: list[PollutionRecord] = []
    pol_report = CleaningReport()
    for provider in build_air_quality_providers(settings):
        try:
            fetched = provider.fetch_window(refs, window_start, hard_end)
            cleaned, cleaned_report = clean_pollution(fetched, now)
            results[f"aq:{provider.code}"] = cleaned_report.summary()
            if cleaned:
                pol_records = cleaned
                pol_report = cleaned_report
                break  # first successful source wins (priority order)
        except Exception as exc:  # noqa: BLE001 - failover is the point here
            results[f"aq:{provider.code}"] = f"unavailable: {exc}"

    wx_records: list[WeatherRecord] = []
    for provider in build_weather_providers(settings):
        try:
            fetched = provider.fetch_window(refs, window_start, hard_end)
            cleaned, cleaned_report = clean_weather(fetched, now)
            results[f"wx:{provider.code}"] = cleaned_report.summary()
            wx_records = cleaned
            break
        except Exception as exc:  # noqa: BLE001
            results[f"wx:{provider.code}"] = f"unavailable: {exc}"

    with factory() as session:
        ins_p, upd_p = write_pollution(session, pol_records, pol_report or CleaningReport())
        ins_w, upd_w = write_weather(session, wx_records)
    results["db:pollution"] = f"inserted={ins_p} updated={upd_p}"
    results["db:weather"] = f"inserted={ins_w} updated={upd_w}"
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest recent NCR air quality + weather")
    parser.add_argument("--hours", type=int, default=72, help="lookback window in hours")
    parser.add_argument("--start", type=str, default=None, help="ISO start (overrides --hours)")
    parser.add_argument("--end", type=str, default=None, help="ISO end (default: now)")
    args = parser.parse_args()

    end = parse_utc(args.end) if args.end else utcnow_naive()
    start = parse_utc(args.start) if args.start else end - timedelta(hours=args.hours)
    print(f"window: {start.isoformat()} -> {end.isoformat()}")

    for key, value in sorted(run(start, end).items()):
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
