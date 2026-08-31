# 06 — Feasibility & Viability

## Technical feasibility — HIGH

| Requirement | Status | Evidence |
|---|---|---|
| Free real-time AQI data for NCR | ✅ | CPCB via data.gov.in (~40+ NCR stations), OpenAQ v3 mirror |
| Free hourly weather | ✅ | Open-Meteo historical+forecast APIs, no key required |
| Historical training depth | ✅ | CPCB archives (2017→present); ERA5 reanalysis back to 1940 |
| Proven model families | ✅ | Gradient boosting widely validated for 1–48 h PM forecasting in literature; deep models optional |
| Student-deployable infra | ✅ | Docker Compose locally; Vercel + free-tier Postgres/VPS in prod |
| Team skills | ✅ | Python/pandas/FastAPI + React/TS are mainstream SIH stack |

**Key risk mitigations**

| Risk | Mitigation |
|---|---|
| CPCB API downtime at demo | Multi-provider fallback chain (OpenAQ → WAQI) + labelled DEMO MODE dataset |
| Sensor gaps/outages degrade features | Explicit imputation policy + quality flags + gap-aware model masking |
| Deep learning overfitting on limited history | Boosting-first policy; DL only promoted if it wins walk-forward validation |
| Leakage bugs inflate metrics | Dedicated leakage test suite; chronological splits enforced in code, not convention |
| Venue Wi-Fi blocks APIs | Demo dataset bundled; offline build of frontend |

## Economic viability — LOW cost, sustainable

- Dev/demo cost: **₹0** (open data, free-tier hosting, local MLflow).
- Steady state: single small VPS (~₹400–800/mo) serves ingestion, DB, API for NCR-scale load.
- Public-sector path: aligns directly with **CAQM/GRAP** predictive needs and NCAP goals — a
  natural adoption route without new hardware (they already run CPCB infrastructure).

## Operational feasibility

- Scheduled Celery jobs (15-min ingest, hourly forecast refresh, nightly quality report).
- One-command local run: `docker compose up`.
- Retraining is automated but **gated**: challenger must beat champion on identical validation;
  otherwise registry keeps current model.

## Timeline feasibility (6 weeks)

| Week | Milestone |
|---|---|
| 1 | Repo, DB schema+migrations, ingestion (AQI + weather) live |
| 2 | Cleaning + validation + feature pipeline; historical dataset built |
| 3 | Baselines + XGBoost trained; walk-forward evaluation harness |
| 4 | Advanced model attempt; uncertainty; explainability; FastAPI complete |
| 5 | Full dashboard: map, forecast, analysis, model intelligence, alerts |
| 6 | Tests green, security pass, docs, demo rehearsal, deployment |

## Legal/licensing

All primary sources are public/open (CPCB open data licence, OpenAQ CC-BY 4.0, Open-Meteo CC-BY 4.0,
ERA5 licence). Attribution displayed in-app ("Data sources" footer). No personal data collected.
