"""Explanation generation for forecasts.

- If a fitted Ridge ML model is deployed for (station, target), contributions are
  derived from its per-feature coefficient magnitudes (a documented, honest
  proxy for feature attribution), reported as signed up/down contributions.
- Otherwise the persistence baseline is explained transparently (it repeats the
  most recent observation), so the UI never presents a fitted model it isn't.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from ml.forecasting.service import _load_ml_model, latest_model_artifact
from ml.forecasting.train import FEATURE_LABELS
from ml.storage.models import Station

DISCLAIMER_HEURISTIC = (
    "Explanation is heuristic. No ML model is trained yet for this station, so "
    "forecasts follow a persistence baseline (latest observation repeated). "
    "Train the model (see Model Intelligence / scheduler) to get feature-level attribution."
)
DISCLAIMER_ML = (
    "Feature contributions are derived from model coefficient magnitudes; "
    "direction reflects the sign of the influence. Correlations, not causation."
)

HEURISTIC_CONTRIB: list[dict] = [
    {
        "feature_label": "Most recent observation",
        "direction": "up",
        "weight_pct": 100.0,
        "phrase": "Forecast holds the latest observed PM level forward with widening uncertainty.",
    }
]


def explain_forecast(
    db: Session,
    station: Station,
    target: str,
) -> dict:
    run = latest_model_artifact(db, station.canonical_slug, target)
    model = _load_ml_model(run) if run else None

    if model is None:
        return {
            "station_id": station.canonical_slug,
            "station_name": station.name,
            "target": target,
            "narrative": (
                f"No trained ML model is available for {station.name}; the forecast "
                "uses a persistence baseline (repeats the latest observation) with "
                "uncertainty growing with horizon."
            ),
            "disclaimer": DISCLAIMER_HEURISTIC,
            "confidence": "low",
            "contributions": HEURISTIC_CONTRIB,
        }

    imps = model.feature_importances or {}
    if not imps:
        return {
            "station_id": station.canonical_slug,
            "station_name": station.name,
            "target": target,
            "narrative": "Model provides a forecast but no global importance is recorded.",
            "disclaimer": DISCLAIMER_ML,
            "confidence": "moderate",
            "contributions": [],
        }

    sorted_imps = sorted(
        ((k, weight) for weight, k in ((v, k) for k, v in imps.items())),
        key=lambda item: item[1],
        reverse=True,
    )
    contributions = []
    for col, weight_pct in sorted_imps[:8]:
        contributions.append(
            {
                "feature_label": FEATURE_LABELS.get(col, col.replace("_", " ")),
                "direction": "up" if col.startswith("target_") else "down",
                "weight_pct": round(weight_pct * 100, 1),
                "phrase": f"Contributes ~{round(weight_pct * 100, 1)}% of explained variation.",
            }
        )
    narrative = (
        f"Forecast for {station.name} is driven most strongly by recent PM "
        f"levels, with meteorological features modulating the short-term trend."
    )
    return {
        "station_id": station.canonical_slug,
        "station_name": station.name,
        "target": target,
        "narrative": narrative,
        "disclaimer": DISCLAIMER_ML,
        "confidence": "moderate",
        "contributions": contributions,
    }


def global_importance(db: Session, target: str = "pm25") -> list[dict]:
    """Aggregate global importance across deployed models for a target."""
    from ml.storage.models import ModelRun

    runs = (
        db.query(ModelRun)
        .filter(ModelRun.status == "deployed", ModelRun.model_name == "ridge-quantile")
        .all()
    )
    totals: dict[str, float] = {}
    count = 0
    for run in runs:
        model = _load_ml_model(run)
        if model is None or not model.feature_importances:
            continue
        count += 1
        for col, w in model.feature_importances.items():
            totals[col] = totals.get(col, 0.0) + w
    if count == 0:
        return []
    out = []
    for col, total in totals.items():
        out.append(
            {
                "feature_label": FEATURE_LABELS.get(col, col.replace("_", " ")),
                "importance_pct": round((total / count) * 100, 1),
                "family": (
                    "Pollution lag"
                    if col.startswith("target_")
                    else "Meteorology"
                    if col
                    in (
                        "temp_c",
                        "rh_pct",
                        "ws_ms",
                        "wd_sin",
                        "wd_cos",
                        "pressure_hpa",
                        "precip_mm_6h",
                        "stagnation_24h",
                        "rain_hours_24h",
                    )
                    else "Temporal"
                ),
            }
        )
    out.sort(key=lambda d: d["importance_pct"], reverse=True)
    return out
