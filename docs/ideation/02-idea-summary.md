# 02 — Idea Summary

**Project name:** AiraCast — Air Pollution–Weather Coupled Forecasting System
**Track:** Clean & Green Technology / Disaster & Safety Management / Data Science for Governance
**Focus region:** Delhi NCR (Delhi, Noida, Greater Noida, Ghaziabad, Gurugram, Faridabad)

## Elevator pitch (30 seconds)

AiraCast ingests live station-level air-quality and weather data across Delhi NCR, engineers
physically meaningful weather–pollution features (dispersion proxies, accumulation conditions,
wind vectors), and trains time-series-aware ML models to forecast **AQI, PM2.5 and PM10** for each
monitoring station over horizons of **1 to 72 hours** — complete with prediction intervals,
explainability ("why is tomorrow's PM2.5 high?"), an alert engine, and an honest model-comparison
dashboard. It is built as a production-grade platform (FastAPI + Next.js + PostgreSQL), not a
notebook demo.

## Core innovation claims

1. **Explicit weather–pollution coupling** as first-class feature engineering — wind-vector
   components, stagnation indicators, rolling meteorological memory — not just concatenated feeds.
2. **Scientifically disciplined model selection**: baselines (persistence → gradient boosting) are
   always benchmarked against advanced models (LSTM/Transformer) under walk-forward validation;
   the simplest model that wins is deployed.
3. **Trust-first UX**: every number is labelled Observed / Forecast / Interpolated / Model-derived;
   forecasts carry intervals; explanations are labelled as associations, not causation.
4. **Data-quality engine**: frozen-sensor detection, spike/outlier screening, outage logging —
   surfaced in the UI rather than hidden.

## What we build (MVP scope)

Live dashboard · interactive NCR map · per-station forecasts · weather–pollution analysis ·
model intelligence page (metrics, SHAP) · alerts · REST API · reproducible training pipeline ·
clearly-labelled demo mode when APIs are unavailable.

## What we deliberately defer (Phase 3 research)

GNNs, spatio-temporal transformers, satellite/AOD fusion, fire/traffic data ingestion, causal
inference — extension interfaces are designed now, implementation deferred.

## Success criterion (measurable)

Beat the persistence baseline on held-out walk-forward validation for ≥90% of active stations at the
24-hour horizon, with all metrics produced from real trained models stored in a model registry —
never hard-coded.
