# 05 — System Architecture

## High-level architecture

```
                        ┌─────────────────────────────────────────────┐
   EXTERNAL SOURCES     │  CPCB (data.gov.in) · OpenAQ · WAQI         │
                        │  Open-Meteo · IMD/OpenWeatherMap            │
                        │  ERA5 / CDS (research mode)                 │
                        └──────────────┬──────────────────────────────┘
                                       │ HTTPS (API keys via env)
                                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│ INGESTION LAYER (Celery beat schedules, per-provider adapters)       │
│  fetch → raw JSONL landing zone → provider normalization             │
│  station-name canonicalization → timezone → Asia/Kolkata             │
└──────────────┬───────────────────────────────────────────────────────┘
               ▼
┌──────────────────────────────────────────────────────────────────────┐
│ VALIDATION & CLEANING                                                 │
│  range checks · spike detection · frozen-sensor detection ·           │
│  duplicate timestamps · gap interpolation policy (labelled!) ·        │
│  data_quality_logs table                                              │
└──────────────┬───────────────────────────────────────────────────────┘
               ▼
┌──────────────────────────────────────────────────────────────────────┐
│ FEATURE ENGINEERING (feature store tables)                            │
│  lags · rolling stats · wind u/v · stagnation flags · rainfall sums · │
│  temporal encodings · holiday flags · upwind-station proxies          │
│  ── STRICTLY causal: only t-1 and earlier may enter features for t    │
└──────────────┬───────────────────────────────────────────────────────┘
               ▼
┌──────────────────────────────────────────────────────────────────────┐
│ ML ENGINE                                                             │
│  walk-forward split → baselines → boosting → sequence models →        │
│  ensemble → Optuna HPO → metrics → MLflow registry → champion model   │
│  quantile models → intervals                                          │
└──────────────┬───────────────────────────────────────────────────────┘
               ▼
┌──────────────────────────────────────────────────────────────────────┐
│ PERSISTENCE — PostgreSQL 16 (+PostGIS)                                │
│  stations · pollution_observations · weather_observations ·           │
│  features · forecasts · model_runs · model_metrics · alerts ·         │
│  data_sources · data_quality_logs                                     │
│  Redis: cache + Celery broker                                         │
└──────────────┬───────────────────────────────────────────────────────┘
               ▼
┌──────────────────────────────────────────────────────────────────────┐
│ FASTAPI BACKEND                                                       │
│  /api/air-quality/*  /api/weather/*  /api/stations*                   │
│  /api/forecast*      /api/model/*    /api/alerts*                     │
│  Pydantic schemas · pagination · ETag/Cache-Control · rate limits     │
└──────────────┬───────────────────────────────────────────────────────┘
               ▼
┌──────────────────────────────────────────────────────────────────────┐
│ NEXT.JS FRONTEND                                                      │
│  Overview · Live Map (MapLibre) · Forecast · Station Explorer ·       │
│  Weather–Pollution Analysis · Model Intelligence · History · Alerts   │
│  Research Mode (CSV export, correlation explorer)                     │
└──────────────────────────────────────────────────────────────────────┘

ALERT ENGINE (Celery task, every 15 min): thresholds on observed+forecast
series → alerts table → dashboard + webhook/e-mail adapters.
```

## Data flow guarantees

1. **No leakage**: feature builder receives only data with `observed_at <= cutoff`; unit tests
   assert no feature column correlates with future rows by construction.
2. **Provenance**: every observation row carries `source_id` + `quality_flag`
   (`raw|cleaned|interpolated`); every forecast carries `model_run_id`.
3. **Idempotent ingestion**: re-running an ingest window upserts; never duplicates.
4. **Degraded-mode honesty**: if a provider fails, the UI shows stale-data age + quality banner,
   or DEMO MODE — it never silently fabricates.

## Station-level vs region-level

- **Training/inference unit:** monitoring station (lat/lon in PostGIS).
- **Map layer:** IDW/Gaussian-kernel interpolation of station values & forecasts onto a grid,
  rendered as raster tiles/vector fill. Interpolated pixels are labelled "Estimated".
- **Future hook:** `SpatialModel` interface allows GNN/kriging replacement without touching API.

## Scaling story (design now, activate later)

- Hundreds of stations: ingestion is per-provider batched upserts; Timescale-style partitioning of
  observation tables by month is pre-planned in the schema doc.
- Multiple cities: everything is keyed by `station.region`; adding a city = adding stations +
  config, zero code change.
- Real-time: swap polling interval down; add WebSocket/SSE channel for dashboard push.
