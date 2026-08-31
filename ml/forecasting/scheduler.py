"""Scheduler: periodically train + persist fresh forecasts for all stations.

Run standalone via `scripts/run_scheduler.py`, or mounted as a FastAPI
lifespan task. A single scheduler process is expected (no distributed workers).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from ml.config.settings import get_settings
from ml.forecasting.service import generate_forecast, persist_forecast
from ml.forecasting.train import train_all
from ml.storage.db import init_schema, make_engine, make_session_factory
from ml.storage.models import Station

logger = logging.getLogger("airacast.scheduler")

TARGETS = ("aqi", "pm25", "pm10", "no2")


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def run_cycle(targets: tuple[str, ...] = TARGETS, train: bool = True) -> dict[str, str]:
    settings = get_settings()
    engine = make_engine(settings)
    init_schema(engine)
    factory = make_session_factory(engine)
    summary: dict[str, str] = {}

    with factory() as db:
        if train:
            trained = train_all(db, targets)
            n_deployed = sum(1 for r in trained if r["status"] == "deployed")
            n_benchmark = sum(1 for r in trained if r["status"] == "benchmark")
            n_baseline = sum(1 for r in trained if r["status"] == "baseline")
            summary["train"] = (
                f"stations={len(trained)} deployed={n_deployed} "
                f"benchmark={n_benchmark} baseline={n_baseline}"
            )

        stations = db.query(Station).filter(Station.is_active.is_(True)).all()
        forecasts = 0
        skipped = 0
        for station in stations:
            for target in targets:
                try:
                    result = generate_forecast(db, station, target, horizons=48, ahead_hours=72)
                    persist_forecast(db, station.canonical_slug, target, result)
                    forecasts += 1
                except ValueError:
                    skipped += 1
                except Exception:  # noqa: BLE001 - keep scheduler alive
                    logger.exception("forecast failed for %s/%s", station.canonical_slug, target)
                    skipped += 1
        summary["forecast"] = f"written={forecasts} skipped={skipped}"

    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(run_cycle())
