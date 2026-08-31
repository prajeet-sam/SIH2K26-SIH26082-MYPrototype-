from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

import httpx

from ml.config.settings import Settings
from ml.providers.base import AirQualityProvider, PollutionRecord, ProviderError, StationRef


def utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

POLLUTANT_FIELDS: dict[str, str] = {
    "pm25": "pm2_5",
    "pm10": "pm10",
    "no2": "nitrogen_dioxide",
    "so2": "sulphur_dioxide",
    "o3": "ozone",
    "co": "carbon_monoxide",
}


class OpenMeteoAirQualityProvider(AirQualityProvider):
    code = "open-meteo-air"
    display_name = "Open-Meteo Air Quality (CAMS model, keyless)"
    requires_key = False

    def __init__(self, settings: Settings, client: httpx.Client | None = None):
        self._settings = settings
        self._client = client

    def is_available(self) -> bool:
        return True

    def _chunk(self, stations: Sequence[StationRef]) -> list[list[StationRef]]:
        size = max(1, self._settings.provider_chunk_size)
        return [list(stations[i : i + size]) for i in range(0, len(stations), size)]

    def fetch_window(
        self, stations: Sequence[StationRef], start_utc: datetime, end_utc: datetime
    ) -> list[PollutionRecord]:
        now = utcnow_naive()
        past_days = max(0, min(92, (now - start_utc).days))
        forecast_days = max(1, min(5, (end_utc - now).days + 1))
        records: list[PollutionRecord] = []
        client = self._client or httpx.Client(timeout=self._settings.http_timeout_seconds)
        try:
            for chunk in self._chunk(stations):
                params: dict[str, Any] = {
                    "latitude": ",".join(f"{s.latitude:.4f}" for s in chunk),
                    "longitude": ",".join(f"{s.longitude:.4f}" for s in chunk),
                    "hourly": ",".join(POLLUTANT_FIELDS.values()),
                    "timezone": "UTC",
                    "past_days": past_days,
                    "forecast_days": forecast_days,
                    "domains": "cams_global",
                }
                try:
                    resp = client.get(AIR_QUALITY_URL, params=params)
                    resp.raise_for_status()
                    payload = resp.json()
                except httpx.HTTPError as exc:
                    raise ProviderError(f"open-meteo air-quality request failed: {exc}") from exc
                records.extend(self.parse_payload(chunk, payload, start_utc, end_utc))
        finally:
            if self._client is None:
                client.close()
        return records

    @staticmethod
    def parse_payload(
        chunk: Sequence[StationRef],
        payload: Any,
        start_utc: datetime,
        end_utc: datetime,
    ) -> list[PollutionRecord]:
        blocks = payload if isinstance(payload, list) else [payload]
        records: list[PollutionRecord] = []
        for station, block in zip(chunk, blocks, strict=False):
            hourly = block.get("hourly", {})
            times: list[str] = hourly.get("time", [])
            for i, ts in enumerate(times):
                observed_at = datetime.strptime(ts, "%Y-%m-%dT%H:%M")
                if observed_at < start_utc.replace(minute=0, second=0, microsecond=0):
                    continue
                if observed_at > end_utc:
                    continue
                for pollutant, field in POLLUTANT_FIELDS.items():
                    series = hourly.get(field) or []
                    if i >= len(series):
                        continue
                    raw = series[i]
                    if raw is None:
                        continue
                    value = float(raw)
                    unit = "ug/m3"
                    if pollutant == "co":
                        value = round(value / 1000.0, 4)
                        unit = "mg/m3"
                    if value < 0:
                        continue
                    records.append(
                        PollutionRecord(
                            station_slug=station.slug,
                            pollutant=pollutant,
                            value=value,
                            unit=unit,
                            observed_at=observed_at,
                            source_code="open-meteo-air",
                        )
                    )
        return records
