from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from ml.config.settings import Settings
from ml.providers.base import ProviderError, StationRef, WeatherProvider, WeatherRecord


def utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HOURLY_FIELDS = [
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
    "precipitation",
    "surface_pressure",
]

MAX_PAST_DAYS = 92


def _cell(series: list, idx: int) -> float | None:
    if idx >= len(series):
        return None
    raw = series[idx]
    return float(raw) if raw is not None else None


class OpenMeteoWeatherProvider(WeatherProvider):
    code = "open-meteo"
    display_name = "Open-Meteo (hourly archive+forecast)"
    requires_key = False

    def __init__(self, settings: Settings, client: httpx.Client | None = None):
        self._settings = settings
        self._client = client

    def is_available(self) -> bool:
        return True

    def _chunk(self, stations: Sequence[StationRef]) -> list[list[StationRef]]:
        size = max(1, self._settings.provider_chunk_size)
        return [list(stations[i : i + size]) for i in range(0, len(stations), size)]

    def _build_params(
        self, chunk: Sequence[StationRef], start_utc: datetime, end_utc: datetime
    ) -> dict[str, Any]:
        now = utcnow_naive()
        past_days = min(MAX_PAST_DAYS, max(0, (now - start_utc).days))
        forecast_days = max(1, min(16, (end_utc - now).days + 2))
        return {
            "latitude": ",".join(f"{s.latitude:.4f}" for s in chunk),
            "longitude": ",".join(f"{s.longitude:.4f}" for s in chunk),
            "hourly": ",".join(HOURLY_FIELDS),
            "timezone": "UTC",
            "past_days": past_days,
            "forecast_days": forecast_days,
        }

    @staticmethod
    def parse_payload(chunk: Sequence[StationRef], payload: Any) -> list[WeatherRecord]:
        blocks = payload if isinstance(payload, list) else [payload]
        records: list[WeatherRecord] = []
        for station, block in zip(chunk, blocks, strict=False):
            hourly = block.get("hourly", {})
            times: list[str] = hourly.get("time", [])
            columns = {
                field: hourly.get(field, [])
                for field in (
                    "temperature_2m",
                    "relative_humidity_2m",
                    "wind_speed_10m",
                    "wind_direction_10m",
                    "wind_gusts_10m",
                    "precipitation",
                    "surface_pressure",
                )
            }
            for i, ts in enumerate(times):
                observed_at = datetime.strptime(ts, "%Y-%m-%dT%H:%M")

                def val(col: str, _i: int = i, _columns: dict = columns) -> float | None:
                    return _cell(_columns.get(col) or [], _i)

                records.append(
                    WeatherRecord(
                        station_slug=station.slug,
                        observed_at=observed_at,
                        temperature_c=val("temperature_2m"),
                        relative_humidity_pct=val("relative_humidity_2m"),
                        wind_speed_ms=val("wind_speed_10m"),
                        wind_direction_deg=val("wind_direction_10m"),
                        wind_gust_ms=val("wind_gusts_10m"),
                        precipitation_mm=val("precipitation"),
                        pressure_hpa=val("surface_pressure"),
                        source_code="open-meteo",
                    )
                )
        return records

    def fetch_window(
        self, stations: Sequence[StationRef], start_utc: datetime, end_utc: datetime
    ) -> list[WeatherRecord]:
        records: list[WeatherRecord] = []
        client = self._client or httpx.Client(timeout=self._settings.http_timeout_seconds)
        try:
            for chunk in self._chunk(stations):
                params = self._build_params(chunk, start_utc, end_utc)
                try:
                    resp = client.get(FORECAST_URL, params=params)
                    resp.raise_for_status()
                    payload = resp.json()
                except httpx.HTTPError as exc:
                    raise ProviderError(f"open-meteo request failed: {exc}") from exc
                records.extend(self.parse_payload(chunk, payload))
        finally:
            if self._client is None:
                client.close()
        cutoff = start_utc - timedelta(minutes=90)
        return [r for r in records if r.observed_at >= cutoff and r.observed_at <= end_utc]
