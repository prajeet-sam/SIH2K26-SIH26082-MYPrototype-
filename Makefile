.PHONY: install lint lint-fix test api seed ingest forecast migrate makemigrations docker-up docker-down

# --- Python ---

install:
	pip install -r requirements.txt

lint:
	ruff check api ml pipelines scripts tests

lint-fix:
	ruff check api ml pipelines scripts tests --fix
	ruff format api ml pipelines scripts tests

test:
	pytest

seed:
	python -m scripts.seed_stations

ingest:
	python -m pipelines.ingest_recent --hours 72

forecast:
	python -m scripts.run_scheduler

migrate:
	alembic upgrade head

makemigrations:
	alembic revision --autogenerate

api:
	uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# --- Docker ---

docker-up:
	docker compose up --build

docker-down:
	docker compose down

# --- Frontend ---

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

frontend-test:
	cd frontend && npm test
