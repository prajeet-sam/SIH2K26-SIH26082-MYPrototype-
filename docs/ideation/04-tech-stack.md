# 04 — Technology Stack

Selection principle: **boring, proven, free/low-cost, deployable by students.** No Kubernetes,
no microservices, no paid-only dependencies in the critical path.

## Frontend

| Concern | Choice | Rationale |
|---|---|---|
| Framework | **Next.js 14+ (App Router) + React 18 + TypeScript (strict)** | SSR-lite, file routing, huge ecosystem |
| Styling | **Tailwind CSS** | Speed, consistency, dark-mode support |
| Charts | **Recharts** (primary) + **ECharts** (heatmap/wind rose if needed) | Declarative TS-friendly charting |
| Maps | **MapLibre GL JS** (open-source, no token required) with raster/vector tiles; Leaflet fallback | Zero vendor lock-in |
| State/data fetching | **TanStack Query** | Caching, retries, loading/error states for free |
| Testing | Vitest + React Testing Library | Fast, modern |

## Backend

| Concern | Choice | Rationale |
|---|---|---|
| Language/framework | **Python 3.11 + FastAPI** | Same language as ML; async; auto OpenAPI docs |
| Validation | Pydantic v2 | Typed request/response schemas |
| ORM/migrations | SQLAlchemy 2.0 + **Alembic** | Versioned schema migrations |
| Auth (Phase 2) | JWT (OAuth2 password flow) for admin/research endpoints | Public read endpoints stay open |
| Rate limiting | slowapi (Redis-backed) | Protect public endpoints |
| Task queue | **Celery + Redis** for scheduled ingestion/training | Cron-like reliability without extra services |
| Testing | pytest + httpx TestClient | Standard |

## Machine Learning

| Concern | Choice | Rationale |
|---|---|---|
| Core | pandas, NumPy, scikit-learn | Baselines + preprocessing |
| Boosting | **XGBoost / LightGBM** | Best effort/accuracy trade-off on tabular weather+pollution features |
| Deep learning | **PyTorch** (LSTM/GRU; PatchTST-style attention optional) | Only adopted if it beats boosting under identical validation |
| Explainability | shap + sklearn permutation_importance | Global + local explanations |
| Experiment tracking | **MLflow** (local file backend) | Runs, params, metrics, artifacts, registry — zero cloud cost |
| Hyperparameters | Optuna (time-aware pruning) | Efficient HPO without leakage |

## Data layer

| Concern | Choice | Rationale |
|---|---|---|
| OLTP/time-series store | **PostgreSQL 16 (+ PostGIS)** | One DB for relational + spatial; BRIN/GIST indexes for time-series |
| Cache | Redis | Hot dashboard queries, rate limiting, Celery broker |
| Air-quality sources | CPCB (data.gov.in API), **OpenAQ v3**, WAQI fallback | Redundancy across providers |
| Weather sources | **Open-Meteo** (free, no key), IMD/OpenWeatherMap optional | Redundancy |
| Reanalysis (research) | ERA5 via Copernicus CDS (boundary-layer height, pressure fields) | Research-mode depth |

## Infrastructure / DevOps

| Concern | Choice |
|---|---|
| Local orchestration | Docker Compose (frontend, backend, db, redis, worker) |
| CI | GitHub Actions: lint (ruff, eslint), typecheck (mypy, tsc), tests |
| Hosting (cheap tier) | Frontend → Vercel/Netlify free tier; Backend+worker → single VPS/Fly.io/Railway; Postgres → Neon/Supabase free tier or VPS docker |
| Secrets | `.env` files (never committed) + `.env.example`; host-provided env vars |
| Monitoring | Structured JSON logs + `/health` endpoints + data-quality dashboard page |

## Explicit non-goals (for now)

Kubernetes · microservice split · Kafka/streaming · paid map/API vendors in critical path ·
mobile apps (responsive web first).
