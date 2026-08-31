"""Run the forecast scheduler once (train + persist forecasts for all stations).

Usage:
    python -m scripts.run_scheduler --no-train
"""

from __future__ import annotations

import argparse
import logging

from ml.forecasting.scheduler import TARGETS, run_cycle


def main() -> None:
    parser = argparse.ArgumentParser(description="AiraCast forecast scheduler")
    parser.add_argument(
        "--no-train",
        action="store_true",
        help="skip model training; only emit forecasts",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    summary = run_cycle(targets=TARGETS, train=not args.no_train)
    for key, value in sorted(summary.items()):
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
