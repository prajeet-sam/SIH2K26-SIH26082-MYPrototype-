"""Seed the database with canonical NCR stations, data sources, and default alert rules.

Usage:
    python -m scripts.seed_stations            # uses AIRACAST_DATABASE_URL / .env
"""

from __future__ import annotations

from ml.config.settings import get_settings
from ml.storage.db import init_schema, make_engine, make_session_factory
from ml.storage.models import AlertRule, DataSource, Station
from ml.storage.station_catalog import STATION_CATALOG
from ml.storage.upsert import upsert_rows

DATA_SOURCES = [
    {"provider_code": "cpcb", "name": "CPCB CAAQMS (via data.gov.in)", "requires_key": True},
    {"provider_code": "openaq", "name": "OpenAQ v3", "requires_key": True},
    {
        "provider_code": "waqi",
        "name": "World Air Quality Index",
        "requires_key": True,
        "base_url": "https://api.waqi.info",
    },
    {
        "provider_code": "open-meteo-air",
        "name": "Open-Meteo Air Quality (CAMS)",
        "requires_key": False,
        "base_url": "https://air-quality-api.open-meteo.com",
    },
    {
        "provider_code": "open-meteo",
        "name": "Open-Meteo Weather",
        "requires_key": False,
        "base_url": "https://api.open-meteo.com",
    },
    {
        "provider_code": "demo",
        "name": "Bundled synthetic air quality (labelled demo)",
        "requires_key": False,
    },
    {
        "provider_code": "demo-wx",
        "name": "Bundled synthetic weather (labelled demo)",
        "requires_key": False,
    },
]

DEFAULT_ALERT_RULES = [
    {
        "name": "pm25_daily_mean_poor",
        "metric": "pm25_mean_24h",
        "comparator": ">=",
        "threshold": 60.0,
        "window_hours": 24,
        "enabled": True,
        "cooldown_minutes": 360,
    },
    {
        "name": "pm25_hourly_severe",
        "metric": "pm25_max_1h",
        "comparator": ">=",
        "threshold": 250.0,
        "window_hours": 1,
        "enabled": True,
        "cooldown_minutes": 120,
    },
]


def seed(engine) -> dict[str, int]:
    factory = make_session_factory(engine)
    counts: dict[str, int] = {}
    with factory() as session:
        station_rows = []
        for s in STATION_CATALOG:
            station_rows.append(
                {
                    "canonical_slug": s["slug"],
                    "name": s["name"],
                    "city": s["city"],
                    "region": "Delhi" if s["city"] == "Delhi" else "NCR",
                    "latitude": s["latitude"],
                    "longitude": s["longitude"],
                    "is_active": True,
                }
            )
        ins, upd = upsert_rows(
            session,
            Station,
            station_rows,
            conflict_cols=["canonical_slug"],
            update_cols=["name", "city", "region", "latitude", "longitude", "is_active"],
        )
        counts["stations"] = ins + upd

        source_rows = [dict(r) for r in DATA_SOURCES]
        ins, _ = upsert_rows(
            session,
            DataSource,
            source_rows,
            conflict_cols=["provider_code"],
            update_cols=["name", "base_url", "requires_key", "is_active"],
        )
        counts["data_sources"] = ins

        rule_rows = [dict(r) for r in DEFAULT_ALERT_RULES]
        ins, _ = upsert_rows(
            session,
            AlertRule,
            rule_rows,
            conflict_cols=["name"],
            update_cols=[
                "metric",
                "comparator",
                "threshold",
                "window_hours",
                "enabled",
                "cooldown_minutes",
            ],
        )
        counts["alert_rules"] = ins
    return counts


def main() -> None:
    settings = get_settings()
    engine = make_engine(settings)
    init_schema(engine)
    counts = seed(engine)
    for table, n in sorted(counts.items()):
        print(f"{table}: {n} rows ensured")
    print(f"database: {settings.database_url}")


if __name__ == "__main__":
    main()
