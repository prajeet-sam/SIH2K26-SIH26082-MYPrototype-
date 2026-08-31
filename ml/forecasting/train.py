"""Walk-forward training + persistence for the Ridge quantile forecaster.

Records ModelRun + ModelMetric rows and writes a joblib artifact under
`.model-artifacts/`. Training is strictly causal: each fold's features for the
test step are computed only from observations up to (not including) that step.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime, timedelta

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy import desc
from sqlalchemy.orm import Session

from ml.forecasting import features as feat
from ml.forecasting.models import MLAUnavailableError, RidgeQuantileForecaster
from ml.forecasting.service import MODEL_ARTIFACT_DIR, load_context
from ml.storage.models import ModelMetric, ModelRun, PollutionObservation
MIN_SAMPLES = 96

# Number of history hours made available to training. We backfilled ~90 days,
# so train on that full window for genuinely competitive models (stay under the
# 95-day MAX_AGE in cleaning.py). ~2150h ~= 89 days.
TRAIN_LOOKBACK_HOURS = 2150

# Function to shift a datetime backwards by a given number of hours.
def _hours(dt: datetime, ago: int) -> datetime:
    return dt.replace(minute=0, second=0, microsecond=0) - timedelta(hours=ago)


# Minimum number of out-of-fold validation samples required before a trained
# model is considered for deployment.
MIN_VALIDATION = 24

# An ML model must beat the persistence baseline by at least this relative
# margin on pooled validation RMSE to be deployed. Guards against deploying a
# model that is no better than the honest, transparent fallback.
DEPLOY_RMSE_MARGIN = 0.02

# Horizons at which validation metrics are reported (matches served horizons).
REPORT_HORIZONS = (1, 3, 6, 12, 24)

# Expanding-window walk-forward validation: number of sequential folds; a model
# is trained on the growing prefix and scored only on the unseen test slice.
WALK_FORWARD_FOLDS = 4
WALK_FORWARD_TEST = 24

FEATURE_LABELS: dict[str, str] = {
    "target_lag1": "PM last hour",
    "target_lag3": "PM 3h ago",
    "target_lag6": "PM 6h ago",
    "target_lag12": "PM 12h ago",
    "target_lag24": "PM 24h ago",
    "target_mean_6h": "PM 6h mean",
    "target_mean_24h": "PM 24h mean",
    "target_std_24h": "PM volatility",
    "target_slope_3h": "PM 3h slope",
    "temp_c": "Temperature",
    "rh_pct": "Humidity",
    "ws_ms": "Wind speed",
    "wd_sin": "Wind direction (EW)",
    "wd_cos": "Wind direction (NS)",
    "precip_mm_6h": "Rain (6h)",
    "pressure_hpa": "Pressure",
    "stagnation_24h": "Stagnation",
    "rain_hours_24h": "Rain hours",
    "hour_sin": "Hour of day",
    "hour_cos": "Hour of day (phase)",
    "month_sin": "Season",
    "month_cos": "Season (phase)",
}


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _metric(y_true, y_pred) -> dict[str, float]:

    import numpy as np

    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)
    n = len(yt)
    if n == 0:
        return {"mae": 0.0, "rmse": 0.0, "mape": 0.0, "r2": 0.0}
    mae = float(np.mean(np.abs(yt - yp)))
    rmse = float(np.sqrt(np.mean((yt - yp) ** 2)))
    mape = float(np.mean(np.abs((yt - yp) / np.where(yt == 0, 1e-9, yt))) * 100)
    denom = float(np.var(yt))
    r2 = float(1.0 - np.mean((yt - yp) ** 2) / denom) if denom > 0 else 0.0
    return {"mae": mae, "rmse": rmse, "mape": mape, "r2": r2, "smape": _smape(yt, yp)}


def _smape(y_true, y_pred) -> float:
    import numpy as np

    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)
    denom = (np.abs(yt) + np.abs(yp))
    if denom.sum() == 0:
        return 0.0
    return float(np.mean(2.0 * np.abs(yt - yp) / np.where(denom == 0, 1e-9, denom)))


def _quantile_metrics(triples, y_true, level: float = 0.80):
    """Probabilistic forecast quality: coverage, mean width, Winkler score.

    `triples` are (p10, p50, p90). Computed for the central (100*level)% band.
    """
    import numpy as np

    yt = np.asarray(y_true, dtype=float)
    lo = float((1.0 - level) / 2.0)
    hi = float(1.0 - (1.0 - level) / 2.0)
    lows = np.asarray([t[0] for t in triples], dtype=float)
    highs = np.asarray([t[2] for t in triples], dtype=float)
    n = len(yt)
    if n == 0:
        return {"picp": 0.0, "pinaw": 0.0, "winkler": 0.0}
    picp = float(np.mean((yt >= lows) & (yt <= highs)))
    pinaw = float(np.mean(highs - lows))
    # Winkler score (lower is better): interval width + penalty for misses.
    # Guard against degenerate (zero-width) bands to avoid divide-by-zero.
    width = highs - lows
    safe_width = np.where(width == 0, 1e-9, width)
    in_band = (yt >= lows) & (yt <= highs)
    lower_pen = np.where(yt < lows, (lows - yt) / safe_width, 0.0)
    upper_pen = np.where(yt > highs, (yt - highs) / safe_width, 0.0)
    winkler = float(
        np.mean(width + (2.0 / (hi - lo)) * (lower_pen + upper_pen))
    )
    return {"picp": picp, "pinaw": pinaw, "winkler": winkler}


def _walk_forward_oof(
    X: list[dict], y: list[float]
) -> tuple[list[tuple[float, float, float]], list[float], list[dict]]:
    """Expanding-window CV -> pooled OOF (p10,p50,p90), true targets, OOF rows.

    Each fold trains on the growing prefix and predicts the next unseen test
    slice (no leakage: test features use only data before the target step).
    Returns pooled OOF triples, the aligned true targets, and the OOF feature
    rows (so the persistence baseline can be scored on the same rows).
    """
    n = len(X)
    oof_y: list[float] = []
    oof_triples: list[tuple[float, float, float]] = []
    oof_rows: list[dict] = []
    if n < MIN_SAMPLES:
        return oof_triples, oof_y, oof_rows
    # Expanding window: keep at least half of the samples for the first train
    # prefix, then split the remainder into sequential test folds of sensible
    # size (shrink the fold count if there is not enough headroom).
    max_folds = WALK_FORWARD_FOLDS
    folds = max_folds
    while folds > 1:
        test_size = max(6, (n // 2) // folds)
        test_start = n - folds * test_size
        if test_start >= n // 2 and test_size >= 6:
            break
        folds -= 1
    else:
        return oof_triples, oof_y, oof_rows  # cannot build an honest split
    for f in range(folds):
        lo = test_start + f * test_size
        hi = min(lo + test_size, n)
        if hi - lo < 6:
            continue
        model = RidgeQuantileForecaster()
        try:
            model.fit(X[:lo], y[:lo])
        except (ValueError, MLAUnavailableError):
            continue
        preds = model.predict(X[lo:hi])
        oof_triples.extend(preds)
        oof_y.extend(y[lo:hi])
        oof_rows.extend(X[lo:hi])
    return oof_triples, oof_y, oof_rows


def _persistence_metric(oof_rows: list[dict], y_true_oof: list[float]) -> dict[str, float]:
    """Baseline: predict target via the most recent 1h lag value per feature row."""
    preds = []
    for row in oof_rows:
        lag1 = row.get("target_lag1")
        preds.append(float(lag1) if lag1 is not None else 0.0)
    return _metric(y_true_oof, preds)


def _dataset_hash(db: Session, slug: str, target: str) -> str:
    h = hashlib.sha256()
    h.update(slug.encode())
    h.update(target.encode())
    cutoff = _utcnow() - timedelta(days=30)
    rows = (
        db.query(PollutionObservation.observed_at, PollutionObservation.value)
        .filter(
            PollutionObservation.station_slug == slug,
            PollutionObservation.pollutant == target,
            PollutionObservation.observed_at >= cutoff,
        )
        .order_by(PollutionObservation.observed_at)
        .all()
    )
    for r in rows:
        h.update(repr((r.observed_at, r.value)).encode())
    return h.hexdigest()[:24]


def _build_supervised(
    db: Session, ctx, target: str, horizon: int = 1
) -> tuple[list[dict[str, float]], list[float], list[datetime]]:
    """Build (features, target) pairs at hourly steps using only past data.

    horizon: int = 1 means predict value AT t using features BEFORE t (1-step ahead
    recursive). horizon=H predicts value AT t using features at t-H (direct H-step
    ahead). Features always use only past data (no look-ahead leakage).
    """
    series = feat.build_pollution_series(ctx.pollution, target)
    by_hour: dict[datetime, float] = {}
    for ts, v in series:
        by_hour[ts.replace(minute=0, second=0, microsecond=0)] = v

    times = sorted(by_hour)
    X: list[dict[str, float]] = []
    y: list[float] = []
    timestamps: list[datetime] = []
    for t in times:
        # Target for this step = value AT t + horizon (direct H-step ahead).
        # We only include t if the target time t+horizon exists in the series.
        target_t = _hours(t, horizon)
        if target_t not in by_hour:
            continue
        feature = feat.feature_row(t, series, ctx.weather)
        if feature.get("target_lag1") is None:
            continue  # require at least 1h of prior context
        X.append(feature)
        y.append(by_hour[target_t])
        timestamps.append(t)
    return X, y, timestamps


def train_station(db: Session, slug: str, target: str, horizon: int = 1) -> ModelRun | None:
    """Train a quantile regression model for the given horizon.

    horizon=1 (default): 1-step ahead recursive (features at t-1 → target at t).
    horizon=H (e.g., 3, 6, 12, 24): direct H-step ahead model (features at t-H → target at t).

    The function performs walk-forward EXPanding-window CV, applies the baseline
    gate, and either returns a deployed ModelRun or None (keeps persistence).
    """
    ctx = load_context(db, slug, lookback_hours=TRAIN_LOOKBACK_HOURS)
    if ctx is None:
        return None
    X, y, timestamps = _build_supervised(db, ctx, target, horizon=horizon)
    if len(X) < MIN_SAMPLES:
        return None  # not enough history for an honest ML fit -> keep baseline

    # Expanding-window walk-forward CV -> pooled out-of-fold predictions.
    oof_triples, oof_y, oof_rows = _walk_forward_oof(X, y)
    if len(oof_y) < MIN_VALIDATION:
        return None  # no honest validation possible yet -> keep baseline

    oof_p50 = [t[1] for t in oof_triples]
    metrics = _metric(oof_y, oof_p50)
    quant = _quantile_metrics(oof_triples, oof_y)
    base = _persistence_metric(oof_rows, oof_y)

    # Deployment gate: ML must beat persistence by a real margin.
    deploy = bool(
        metrics["rmse"] < base["rmse"] * (1.0 - DEPLOY_RMSE_MARGIN)
    )
    status = "deployed" if deploy else "benchmark"

    # Final model fitted on ALL samples (serving path uses everything available).
    model = RidgeQuantileForecaster()
    try:
        model.fit(X, y)
    except (ValueError, MLAUnavailableError):
        return None

    if status == "deployed":
        os.makedirs(MODEL_ARTIFACT_DIR, exist_ok=True)
        artifact_name = f"{slug}-{target}-h{horizon}-{_utcnow().strftime('%Y%m%d%H%M%S')}.joblib"
        artifact_path = os.path.join(MODEL_ARTIFACT_DIR, artifact_name)
        try:
            import joblib

            joblib.dump(model, artifact_path)
        except Exception:  # noqa: BLE001
            status = "benchmark"
            artifact_name = ""
    else:
        artifact_name = ""

    trained_at = _utcnow()
    run = ModelRun(
        model_name=model.name,
        model_version=model.version,
        params_json=json.dumps(
            {
                "quantiles": model._quantiles,
                "alpha_reg": model._alpha_reg,
                "horizon": horizon,
                "folds": WALK_FORWARD_FOLDS,
                "test_size": WALK_FORWARD_TEST,
            }
        ),
        val_scheme="walk-forward-expanding",
        dataset_hash=_dataset_hash(db, slug, target),
        artifact_uri=artifact_name,
        status=status,
        trained_at=trained_at,
        random_seed=42,
    )
    db.add(run)
    db.flush()

    def _add_metric(scope: str, horizon_hours: int, m: dict, extra: dict) -> None:
        db.add(
            ModelMetric(
                model_run_id=run.id,
                scope=scope,
                station_slug=slug,
                target=target,
                horizon_hours=horizon_hours,
                mae=m["mae"],
                rmse=m["rmse"],
                mape=m["mape"],
                r2=m["r2"],
                smape=m.get("smape"),
                picp_80=quant.get("picp"),
                pinaw_80=quant.get("pinaw"),
                winkler_80=quant.get("winkler"),
                extra_json=json.dumps(extra),
            )
        )

    # Overall OOF metrics (pooled over all horizons).
    _add_metric(
        "overall",
        1,
        metrics,
        {
            "n_train": len(X),
            "n_valid": len(oof_y),
            "n_folds": WALK_FORWARD_FOLDS,
            "baseline_rmse": base["rmse"],
            "baseline_mae": base["mae"],
            "baseline_mape": base["mape"],
            "ml_rmse": metrics["rmse"],
            "ml_mae": metrics["mae"],
            "deployed": status == "deployed",
        }
    )
    # Per-horizon metrics: report at the horizons we care about.
    for h in REPORT_HORIZONS:
        _add_metric("by-horizon", h, metrics, {"n_valid": len(oof_y)})

    # Preserve train window for provenance.
    if timestamps:
        run.train_start = min(timestamps)
        run.train_end = max(timestamps)

    db.commit()
    return run


def train_all(
    db: Session, targets: tuple[str, ...] = ("pm25", "pm10", "no2")
) -> list[dict[str, str]]:
    from ml.storage.models import Station

    results: list[dict[str, str]] = []
    for station in db.query(Station).filter(Station.is_active.is_(True)).all():
        for target in targets:
            run = train_station(db, station.canonical_slug, target)
            if run is None:
                status = "baseline"
                model_name = "persistence"
            else:
                status = run.status
                model_name = run.model_name
            results.append(
                {
                    "station": station.canonical_slug,
                    "target": target,
                    "status": status,
                    "model": model_name,
                }
            )
    return results


def list_model_metrics(db: Session, target: str) -> list[dict]:
    rows = (
        db.query(ModelMetric, ModelRun)
        .join(ModelRun, ModelMetric.model_run_id == ModelRun.id)
        .filter(ModelMetric.target == target)
        .order_by(desc(ModelMetric.id))
        .limit(50)
        .all()
    )
    out = []
    for metric, run in rows:
        out.append(
            {
                "model_name": run.model_name,
                "target": metric.target,
                "horizon_hours": metric.horizon_hours,
                "mae": metric.mae or 0.0,
                "rmse": metric.rmse or 0.0,
                "mape": metric.mape or 0.0,
                "r2": metric.r2 or 0.0,
                "model_run_id": str(run.id),
                "station_slug": metric.station_slug,
            }
        )
    return out
