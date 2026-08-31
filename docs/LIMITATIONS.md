# Known Limitations & How Integrity Is Preserved

This document records honest, current constraints (see MASTER_OPENCODE_PROMPT.md
§30: no fabricated metrics, no data leakage, demo-mode honesty).

## Forecasting

- **Only a small historical window exists.** CPCB/OpenAQ supply recent
  observations; Open-Meteo has a ~90-day archive. Without a multi-month history,
  gradient/Mal ML models cannot be trained meaningfully per station. Therefore:
  - Training is attempted only when ≥96 hourly feature rows exist.
  - Otherwise, the API returns a **persistence baseline** (latest observation
    repeated with widening uncertainty) that is **explicitly labelled** in the
    `explain` response and `confidence=low`. No ML model is claimed when none ran.
- **Optional native ML stack.** `scikit-learn`/`scipy` are optional imports. If
  their native binaries are unavailable (e.g. blocked by an OS Application
  Control policy), training gracefully degrades to the baseline instead of
  erroring. On a normal host, the Ridge-quantile forecaster trains normally.

## Model performance / feature importance

- `/api/model/performance` and `/api/model/explanations/global-importance`
  return real, persisted metrics only. On a fresh database with no trained
  models they return an **empty list** rather than fabricated numbers. Train and
  run the scheduler to populate them.

## Correlations (research)

- Correlations are computed from whatever aligned hourly observations exist for
  the requested station/days. With sparse weather overlap they return 0.0 for
  pairs lacking ≥3 co-occurring points. This is a data-availability artifact,
  not a bug.

## Feeds & live vs demo

- When `NEXT_PUBLIC_DATA_SOURCE=demo` or the backend API is unreachable, the
  frontend switches to a labelled synthetic dataset. The UI always shows a
  "Demo data" indicator and never presents demo numbers as live observations.
- Alert **rules CRUD** requires `AIRACAST_ADMIN_TOKEN`; without it, POST/PUT
  return 501. Rule *evaluation* is a future phase.

## Other

- Redis caching and Celery queues referenced in the architecture are scaffolded
  but not yet wired into hot paths (the API is already fast without them).
- The map uses MapLibre GL with a free raster tile source; no token required,
  rural detail is limited.
- Forecasts are served from the `forecasts` table populated by the scheduler; if
  the /api forecast is hit before the first scheduler run, it generates and
  persists on demand (slower first call per station).
