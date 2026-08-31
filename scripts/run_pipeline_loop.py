"""Self-contained pipeline scheduler daemon (no Celery/Redis required).

Runs two recurring jobs until stopped:

* Ingest    -- pull recent observations from providers into storage
               (via `pipelines.ingest_recent`) every INGEST_INTERVAL_MIN.
* Forecast  -- train + persist fresh forecasts for all stations
               (via `scripts.run_scheduler` cycle) every FORECAST_INTERVAL_MIN.

This is deliberately a single long-lived process (as the forecasting scheduler
docs assume) using only the Python standard library, suitable for local/dev and
single-host Windows task-scheduler use. It survives provider outages (each run
is wrapped) and logs to a rotating file.

Configuration (constants here, overridable via environment variables):
    AIRACAST_INGEST_MIN    (default 15)
    AIRACAST_FORECAST_MIN  (default 60)
    AIRACAST_TRAIN_MIN     (default 1440, i.e. daily)
    AIRACAST_WORKER_LOG    (default scripts/../pipeline_scheduler.log)
"""

from __future__ import annotations

import logging
import os
import sys
import time
from datetime import UTC, datetime, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

INGEST_MIN = int(os.getenv("AIRACAST_INGEST_MIN", "15"))
FORECAST_MIN = int(os.getenv("AIRACAST_FORECAST_MIN", "60"))
TRAIN_MIN = int(os.getenv("AIRACAST_TRAIN_MIN", "1440"))
LOG_PATH = Path(os.getenv("AIRACAST_WORKER_LOG", str(REPO_ROOT / "pipeline_scheduler.log")))

logger = logging.getLogger("airacast.scheduler_daemon")


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _setup_logging() -> None:
    fmt = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    handler = RotatingFileHandler(
        LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=2, encoding="utf-8"
    )
    handler.setFormatter(fmt)
    root.addHandler(handler)

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    root.addHandler(console)


def run_ingest() -> dict[str, str]:
    from pipelines.ingest_recent import run as _ingest_run

    end = _utcnow()
    start = end - timedelta(hours=72)
    return _ingest_run(start, end)


def run_forecast(train: bool = False) -> dict[str, str]:
    from ml.forecasting.scheduler import TARGETS, run_cycle

    return run_cycle(targets=TARGETS, train=train)


def main() -> None:
    _setup_logging()
    logger.info(
        "AiraCast pipeline scheduler starting (ingest=%s min, forecast=%s min, train=%s min)",
        INGEST_MIN, FORECAST_MIN, TRAIN_MIN,
    )

    next_ingest = time.time()
    next_forecast = time.time() + 60  # stagger the first forecast shortly after boot
    next_train = time.time() + 120    # first training shortly after boot (model bake-in)
    try:
        while True:
            now = time.time()

            if now >= next_ingest:
                logger.info("ingest cycle start")
                try:
                    summary = run_ingest()
                    for k, v in sorted(summary.items()):
                        logger.info("ingest %s=%s", k, v)
                except Exception:  # noqa: BLE001 - keep the daemon alive
                    logger.exception("ingest cycle failed")
                next_ingest = time.time() + INGEST_MIN * 60

            if now >= next_train:
                logger.info("training cycle start")
                try:
                    summary = run_forecast(train=True)
                    for k, v in sorted(summary.items()):
                        logger.info("train_forecast %s=%s", k, v)
                except Exception:  # noqa: BLE001
                    logger.exception("training cycle failed")
                next_train = time.time() + TRAIN_MIN * 60
                next_forecast = now  # refresh forecasts immediately after retraining

            if now >= next_forecast:
                logger.info("forecast cycle start")
                try:
                    summary = run_forecast(train=False)
                    for k, v in sorted(summary.items()):
                        logger.info("forecast %s=%s", k, v)
                except Exception:  # noqa: BLE001
                    logger.exception("forecast cycle failed")
                next_forecast = time.time() + FORECAST_MIN * 60

            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("scheduler stopped by user")


if __name__ == "__main__":
    main()
