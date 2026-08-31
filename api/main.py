from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from time import monotonic

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.routes import (
    air_quality,
    alerts,
    forecast,
    models,
    research,
    stations,
    stations_extra,
    weather,
)
from ml.config.settings import get_settings
from ml.storage.db import init_schema, make_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    engine = make_engine(settings)
    init_schema(engine)
    yield


app = FastAPI(
    title="AiraCast",
    description="NCR air pollution + weather forecasting API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory rate limiter: 100 requests per minute per IP
_request_times: dict[str, list[float]] = {}


def _check_rate_limit(client_ip: str, max_requests: int = 100, window_sec: int = 60) -> None:
    now = monotonic()
    times = _request_times.setdefault(client_ip, [])
    # Remove timestamps outside the window
    while times and now - times[0] > window_sec:
        times.pop(0)
    if len(times) >= max_requests:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    times.append(now)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    _check_rate_limit(request.client.host)
    response = await call_next(request)
    return response

app.include_router(stations.router)
app.include_router(stations_extra.router)
app.include_router(air_quality.router)
app.include_router(weather.router)
app.include_router(alerts.router)
app.include_router(forecast.router)
app.include_router(models.router)
app.include_router(research.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "airacast"}
