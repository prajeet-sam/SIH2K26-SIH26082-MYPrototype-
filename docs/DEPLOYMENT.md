# Deployment

AiraCast is designed to run locally with SQLite (zero-config demo) and on a
cheap cloud host with PostgreSQL 16 + PostGIS via Docker Compose.

## Prerequisites

- Python 3.11+
- Node 20+
- (Docker path) Docker + Docker Compose

## 1. Local (SQLite) — fastest

```bash
python -m venv .venv
. .venv\Scripts\activate          # Windows PowerShell
# . .venv/bin/activate           # macOS/Linux
pip install -r requirements.txt

cp .env.example .env             # review, set AIRACAST_ADMIN_TOKEN etc.

python -m scripts.seed_stations   # 54 NCR stations + data sources + rules
python -m pipelines.ingest_recent --hours 72    # fetch real observations
python -m scripts.run_scheduler   # train (if eligible) + persist forecasts

uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
# http://127.0.0.1:8000/docs

cd frontend
npm install
npm run dev                       # http://127.0.0.1:3000
```

Configure `frontend/.env.local` to point at the API:

```
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_DATA_SOURCE=live
```

## 2. Docker Compose (Postgres + Redis + API + worker + frontend)

```bash
docker compose up --build
```

- API: http://localhost:8000/docs
- Frontend: http://localhost:3000
- `db`: PostGIS 16 (data persisted in the `postgres-data` volume)
- `worker`: runs the forecast scheduler in a loop

Run migrations on the Postgres database:

```bash
docker compose exec api alembic upgrade head
```

## Environment variables

See `.env.example`. Key settings:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy URL (`sqlite:///data/airacast.db` or `postgresql+psycopg://...`) |
| `AIRACAST_DEMO` / `demo_mode` | Forces labelled demo data path |
| `AIRACAST_ADMIN_TOKEN` | Bearer token for alert-rules CRUD (POST/PUT) |
| `NEXT_PUBLIC_API_BASE_URL` | Frontend → API base URL |
| `NEXT_PUBLIC_DATA_SOURCE` | `live` or `demo` |
| `DATA_GOV_IN_API_KEY` | (optional) CPCB API key on data.gov.in |
| `WAQI_API_TOKEN` | (optional) WAQI token |
| `OPENAQ_API_KEY` | (optional) OpenAQ key |

## Scheduling

Run the scheduler on a timer (cron/systemd/Celery beat):

```bash
# one full cycle (train + forecast)
python -m scripts.run_scheduler

# forecast only (skip retraining)
python -m scripts.run_scheduler --no-train
```

It train ML models only for stations with enough history; otherwise it emits a
labelled persistence-baseline forecast. Forecasts are stored in the
`forecasts` table and served by the API (on-demand generation auto-falls back
if the scheduler has not run yet).

## Database migrations (Alembic)

```bash
alembic upgrade head          # apply migrations
alembic revision --autogenerate -m "describe change"   # new migration
```
