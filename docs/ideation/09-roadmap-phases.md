# 09 — Roadmap: MVP → Phase 2 → Phase 3

## MVP (SIH demo scope) — must be fully working

1. NCR station registry (~55 stations) with metadata + PostGIS geometry.
2. Automated ingestion: CPCB/OpenAQ (air) + Open-Meteo (weather), 15-min cadence.
3. Validation/cleaning pipeline with quality flags + data_quality_logs.
4. Feature engineering (lags, rolling stats, wind vectors, stagnation proxies, temporal encodings).
5. Baselines trained: persistence, seasonal-naive, rolling mean, ridge.
6. XGBoost/LightGBM per horizon {1,3,6,12,24,48 h} with walk-forward validation.
7. One deep model (LSTM/GRU or PatchTST-lite) honestly benchmarked.
8. Quantile intervals + confidence labels.
9. FastAPI: full endpoint set incl. `/api/forecast/{station_id}`, `/api/model/performance`,
   `/api/model/explanations`, `/api/alerts`.
10. Next.js dashboard: Overview, Live Map (interpolated heatmap), Forecast charts,
    Station Explorer, Weather–Pollution Analysis, Model Intelligence (real metrics + SHAP),
    Historical Analysis, Alerts page.
11. Alert engine (threshold + rapid-rise rules).
12. Research mode: date-range selection, correlation explorer, CSV export.
13. DEMO MODE with bundled labelled synthetic dataset.
14. Tests (unit/integration/ML-leakage), CI, docs, docker-compose.

## Phase 2 (post-SIH hardening)

- JWT auth for subscriptions/admin; user alert channels (e-mail/Telegram).
- Automated retraining loop with champion/challenger gating + drift monitors (PSI/KS on features,
  rolling error tracking on targets).
- Multi-pollutant forecasts beyond AQI/PM (NO₂, O₃).
- WebSocket/SSE live push; PWA install + push notifications.
- Regional transport proxy upgrade (upwind-station lag matrix learned from data).

## Phase 3 (research-grade extensions)

- Graph Neural Network over station adjacency; spatio-temporal transformer.
- Satellite AOD (MODIS/VIIRS) fusion; fire/thermal-anomaly detection for stubble season.
- Traffic density and land-use regression covariates.
- Numerical weather model features (WRF/GFS downstream) instead of pure reanalysis.
- Probabilistic ensemble forecasting (proper scoring rules: CRPS); conformal prediction.
- Causal-inference studies (effect of rainfall events / GRAP interventions).
- Multi-city rollout template (Mumbai, Kolkata, Bengaluru).

## Explicit non-goals

Real-time sensor hardware deployment · proprietary data purchases · mobile-native apps ·
operational health-advice claims beyond standard AQI category guidance.
