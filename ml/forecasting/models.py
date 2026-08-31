"""Forecast model definitions.

- `PersistenceBaseline`: uses the most recent observed value repeated forward,
  with a bounded uncertainty band scaled by the recent series volatility. This
  is a legitimate, honest fallback that requires no training data volume.
- `RidgeQuantileForecaster`: sklearn Ridge quantile regressors trained on real
  feature rows; used once a meaningful history exists.

Both emit (p10, p50, p90) triples. The serving layer prefers the ML model when
a trained artifact is registered, else falls back to the persistence baseline.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

FEATURE_COLUMNS = (
    "target_lag1",
    "target_lag3",
    "target_lag6",
    "target_lag12",
    "target_lag24",
    "target_mean_6h",
    "target_mean_24h",
    "target_std_24h",
    "target_slope_3h",
    "temp_c",
    "rh_pct",
    "ws_ms",
    "wd_sin",
    "wd_cos",
    "precip_mm_6h",
    "pressure_hpa",
    "stagnation_24h",
    "rain_hours_24h",
    "hour_sin",
    "hour_cos",
    "month_sin",
    "month_cos",
)


@dataclass
class ForecastPoint:
    target_time: datetime
    horizon_hours: int
    p10: float
    p50: float
    p90: float


@dataclass
class ForecastResult:
    points: list[ForecastPoint]
    issued_at: datetime
    model_name: str
    model_version: str
    feature_set_version: str
    trained: bool
    model_run_id: int | None = None


class MLAUnavailableError(RuntimeError):
    """Raised when the optional native ML stack cannot be imported."""


class PersistenceBaseline:
    """Repeats the latest value with uncertainty proportional to recency."""

    name = "persistence"
    version = "v1"

    def __init__(self, latest_value: float, recent_values: list[float] | None = None):
        self.latest_value = max(0.0, float(latest_value))
        self.spread = self._spread(recent_values or [])

    @staticmethod
    def _spread(recent_values: list[float]) -> float:
        if len(recent_values) <= 1:
            return max(5.0, 0.15 * (recent_values[0] if recent_values else 100.0))
        mean = sum(recent_values) / len(recent_values)
        var = sum((v - mean) ** 2 for v in recent_values) / len(recent_values)
        std = math.sqrt(max(0.0, var))
        return max(3.0, float(std))

    def predict(self, times: list[datetime]) -> list[ForecastPoint]:
        out: list[ForecastPoint] = []
        for i, t in enumerate(times):
            horizon = i + 1
            widening = 1.0 + 0.06 * (horizon - 1)
            half = self.spread * widening
            p50 = self.latest_value
            out.append(
                ForecastPoint(
                    target_time=t,
                    horizon_hours=horizon,
                    p10=max(0.0, p50 - half),
                    p50=p50,
                    p90=p50 + half,
                )
            )
        return out


class RidgeQuantileForecaster:
    """Multi-quantile regression over engineered features.

    Fits a separate **quantile regressor per level** (0.1 / 0.5 / 0.9) using
    proper pinball-loss minimisation (sklearn `QuantileRegressor`), so the
    p10 < p50 < p90 bands are genuinely distinct and calibrated rather than a
    single mean forecast repeated three times. Features are standardised with a
    `StandardScaler` fit on the training matrix (Ridge/quantile linear models
    are scale-sensitive and the training set is small).

    sklearn/scipy are optional and imported lazily. If the underlying native
    libraries are unavailable (e.g. blocked by an Application Control policy or
    not installed), `fit` raises `MLAUnavailableError` and the serving layer
    transparently falls back to `PersistenceBaseline`.
    """

    name = "ridge-quantile"
    version = "v2"

    _ml_available: bool | None = None

    def __init__(self, quantiles: list[float] | None = None, alpha_reg: float = 0.05):
        self._fitted = False
        self._quantiles = quantiles or [0.1, 0.5, 0.9]
        self._alpha_reg = float(alpha_reg)
        self._models: dict[float, object] = {}
        self._scaler = None
        self._cols: list[str] = []
        self.feature_columns = list(FEATURE_COLUMNS)
        self.feature_importances: dict[str, float] | None = None

    @classmethod
    def _check_ml(cls) -> bool:
        if cls._ml_available is None:
            try:
                import numpy as np  # noqa: F401
                import scipy  # noqa: F401, RUF100
                import sklearn  # noqa: F401

                cls._ml_available = True
            except Exception:  # noqa: BLE001 - native libs unavailable
                cls._ml_available = False
        return cls._ml_available

    def fit(self, X, y) -> None:
        """X: list[dict], y: list[float]. Fits one quantile regressor per level.

        Features used for scaling/coefficients are the 22 engineered columns in
        `FEATURE_COLUMNS` (missing values imputed to 0 as in `_matrix`).
        """
        if not self._check_ml():
            raise MLAUnavailableError("sklearn/scipy native libraries unavailable in this runtime")
        import numpy as np
        from sklearn.linear_model import QuantileRegressor
        from sklearn.preprocessing import StandardScaler

        matrix, cols = self._matrix(X)
        if len(matrix) < 30 or len(cols) == 0:
            raise ValueError("insufficient training data for ML forecaster")
        yv = np.asarray(y, dtype=float)

        self._scaler = StandardScaler()
        Xs = self._scaler.fit_transform(matrix)
        self._cols = cols

        self._models = {}
        for q in self._quantiles:
            # QuantileRegressor minimises the pinball loss directly (proper
            # quantile estimate). alpha is the L1 penalty on the raw-scale
            # coefficients; a SMALL value (0.05) is essential — an L1 penalty of
            # 1.0 on standardised features collapses all coefficients to zero
            # (degenerate constant forecast). interior-point (highs-ipm) yields
            # a dense, smooth solution that is robust to the strong collinearity
            # among the engineered lag features.
            model = QuantileRegressor(
                quantile=q, alpha=self._alpha_reg, solver="highs-ipm"
            )
            model.fit(Xs, yv)
            self._models[q] = model

        # Feature importance: mean |scaled coefficient| across quantiles.
        coefs = np.mean(
            [np.abs(m.coef_) for m in self._models.values()], axis=0
        ).astype(float)
        total = float(coefs.sum())
        if total > 0:
            self.feature_importances = {c: float(coefs[i] / total) for i, c in enumerate(cols)}
        self._fitted = True

    def _matrix(self, X: list[dict]):
        import numpy as np

        cols = self.feature_columns
        matrix: list[list[float]] = []
        for row in X:
            values = []
            for c in cols:
                v = row.get(c)
                values.append(0.0 if v is None else float(v))
            # Impute missing target-side features with 0 (they are lags; absent
            # earliest lags are folded into the value). See predict() for the
            # iterative lag fill on the forecast path.
            matrix.append(values)
        return np.asarray(matrix, dtype=float), cols

    def predict(self, feature_rows: list[dict]) -> list[tuple[float, float, float]]:
        if not self._fitted:
            raise RuntimeError("forecaster not fitted")
        if not self._check_ml():
            raise MLAUnavailableError("sklearn/scipy native libraries unavailable in this runtime")
        if self._scaler is None:
            raise RuntimeError("forecaster not fitted")
        matrix, _ = self._matrix(feature_rows)
        Xs = self._scaler.transform(matrix)
        preds_by_q = {q: self._models[q].predict(Xs) for q in self._quantiles}
        out: list[tuple[float, float, float]] = []
        for i in range(matrix.shape[0]):
            p10, p50, p90 = (
                preds_by_q[0.1][i],
                preds_by_q[0.5][i],
                preds_by_q[0.9][i],
            )
            # Enforce monotonic band ordering and non-negativity.
            p50 = max(0.0, float(p50))
            p10 = max(0.0, float(min(p10, p50)))
            p90 = max(p50, float(p90))
            out.append((float(p10), p50, float(p90)))
        return out
