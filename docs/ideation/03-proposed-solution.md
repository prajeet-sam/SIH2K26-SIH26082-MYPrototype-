# 03 — Proposed Solution

## Solution overview

AiraCast is a **modular-monolith environmental intelligence platform** with five layers:

```
┌────────────────────────────────────────────────────────────────────┐
│  PRESENTATION   Next.js + TypeScript dashboard, MapLibre map,      │
│                 charts, research mode, alert center                │
├────────────────────────────────────────────────────────────────────┤
│  API LAYER      FastAPI: current/history/forecast/explain/alerts   │
├────────────────────────────────────────────────────────────────────┤
│  INTELLIGENCE   ML engine: baselines → advanced models → ensemble; │
│                 walk-forward validation; registry; SHAP; quantiles │
├────────────────────────────────────────────────────────────────────┤
│  DATA ENGINE    Ingestion (CPCB/OpenAQ + Open-Meteo/IMD) →         │
│                 validation → cleaning → feature store              │
├────────────────────────────────────────────────────────────────────┤
│  STORAGE        PostgreSQL (+PostGIS) time-series schema;          │
│                 data-quality logs; model registry tables           │
└────────────────────────────────────────────────────────────────────┘
```

## How the weather–pollution coupling works

Pollution in NCR is governed by two regimes:

1. **Accumulation regime** — low wind, cool temperatures, high humidity, stable nights
   (winter inversions): emissions accumulate faster than they disperse.
2. **Ventilation/washout regime** — strong winds or significant rainfall: pollution drops.

AiraCast encodes these physics into features rather than hoping a model discovers them:

| Physical concept | Engineered feature |
|---|---|
| Horizontal dispersion | `wind_speed` + lagged/rolling stats; **u/v wind-vector components** from speed+direction |
| Atmospheric stagnation | rolling mean wind speed below thresholds over 6–24 h windows |
| Accumulation memory | 6/12/24 h rolling means & std of PM2.5, PM10, NO₂ |
| Washout | rainfall accumulation over 3/6/24 h |
| Thermal stability | temperature change (`t2m_t - t2m_{t-24h}`), day-night amplitude proxies |
| Moisture effects | humidity lags + rolling means (hygroscopic growth of aerosols) |
| Temporal cycles | hour-of-day sin/cos, day-of-week, month, season, festival/holiday flags |
| Regional transport (proxy) | upwind-station lagged PM (neighbours within radius, weighted by alignment with wind direction) |

Boundary-layer height / inversion proxies are used **only when reliable data exists**
(e.g., ERA5 boundary-layer height for research mode); we never fabricate variables.

## Forecasting approach

```
Persistence / seasonal-naive ─┐
Rolling-mean baseline         ├─→ benchmark table
Ridge/Lasso regression       ─┘
Random Forest                 ─┐
XGBoost / LightGBM            ├─→ candidate models (per horizon)
LSTM or GRU sequence model    │
PatchTST-style transformer    │   (only if data volume justifies)
Ensemble / stacking          ─┘
                              ↓
        Walk-forward validation → metrics (MAE/RMSE/R²/MAPE)
                              ↓
        Winner per station×horizon stored in model registry
                              ↓
        Quantile models / residual intervals for uncertainty
```

**Rule:** deep learning is *not* assumed superior. It must beat tuned gradient boosting under the
same validation protocol to be selected. All comparisons are published on the Model Intelligence page.

## Uncertainty

- Gradient-boosted **quantile regression** (P10/P50/P90) as primary interval method.
- Ensemble spread as secondary signal.
- Confidence label (High/Moderate/Low) derived from recent validation error at that horizon +
   input-data freshness. If intervals cannot yet be trusted, UI says so explicitly.

## Explainability

- Permutation importance (global), SHAP (local, per forecast).
- Natural-language explanation assembled from top contributions:
  *"High PM2.5 expected tonight: calm winds (≤1.5 m/s past 6 h), high humidity, elevated evening
  PM2.5, no rainfall expected."* — labelled as **model-derived association, not causal proof**.

## Alerts

Configurable threshold engine on both observed and forecast series: AQI category crossings,
rapid-rise detection (e.g., ΔPM2.5 > X µg/m³ in 3 h), extreme-event forecasts, data-outage alerts.
Delivered via dashboard + webhook/e-mail stubs.

## Demo mode

If live APIs are unreachable (venue Wi-Fi!), the system runs on a bundled, clearly-labelled
synthetic dataset with a persistent banner: **"Demo data — not real-time observations."**

## Why this solution wins vs alternatives

| Alternative | Why insufficient | AiraCast advantage |
|---|---|---|
| SAFAR/IITM bulletins | City-level, limited horizons, not interactive | Station-level 1–72 h, explainable |
| IQAir/AQICN dashboards | Current-state only | Forward-looking + weather coupling |
| Generic "AQI predictor" notebooks | No pipeline, leakage-prone, no deployment | Reproducible MLOps + production stack |
