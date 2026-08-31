"""WAQI adapter (feed by geo coordinates, token-gated).

Returns pollutant concentrations from the `iaqi` block where available; the
scalar `data.aqi` index is intentionally NOT ingested as a concentration.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

import httpx

from ml.config.settings import Settings
from ml.providers.base import AirQualityProvider, PollutionRecord, ProviderError, StationRef
from ml.storage.station_catalog import STATION_CATALOG

FEED_URL = "https://api.waqi.info/feed/geo:{lat};{lon}/"

IAQI_MAP = {"pm25": "pm25", "pm10": "pm10", "no2": "no2", "so2": "so2", "o3": "o3", "co": "co"}

# WAQI iaqi concentrations are ug/m3 except CO which it reports in mg/m3.
UNIT_BY_POLLUTANT = {p: ("mg/m3" if p == "co" else "ug/m3") for p in IAQI_MAP}


def _nearest_slug(lat: float, lon: float) -> str | None:
    best: tuple[float, str] | None = None
    for s in STATION_CATALOG:
        d = ((s["latitude"] - lat) ** 2 + ((s["longitude"] - lon) * 0.87) ** 2) ** 0.5
        if d < 0.06 and (best is None or d < best[0]):
            best = (d, s["slug"])
    return best[1] if best else None


class WaqiProvider(AirQualityProvider):
    code = "waqi"
    display_name = "World Air Quality Index"
    requires_key = True

    def __init__(self, settings: Settings, client: httpx.Client | None = None):
        self._settings = settings
        self._client = client

    def is_available(self) -> bool:
        return bool(self._settings.waqi_api_token)

    def fetch_window(
        self, stations: Sequence[StationRef], start_utc: datetime, end_utc: datetime
    ) -> list[PollutionRecord]:
        del stations  # WAQI is queried per catalog coordinate
        records: list[PollutionRecord] = []
        client = self._client or httpx.Client(timeout=self._settings.http_timeout_seconds)
        try:
            for s in STATION_CATALOG:
                records.extend(self._fetch_point(client, s["slug"], s["latitude"], s["longitude"]))
        finally:
            if self._client is None:
                client.close()
        return [r for r in records if r.observed_at <= end_utc]

    def _fetch_point(
        self, client: httpx.Client, slug_hint: str, lat: float, lon: float
    ) -> list[PollutionRecord]:
        try:
            resp = client.get(
                FEED_URL.format(lat=f"{lat:.4f}", lon=f"{lon:.4f}"),
                params={"token": self._settings.waqi_api_token},
            )
            resp.raise_for_status()
            payload = resp.json()
        except httpx.HTTPError as exc:
            raise ProviderError(f"waqi request failed: {exc}") from exc
        if payload.get("status") != "ok":
            return []
        data = payload.get("data") or {}

        observed_at = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        iso_time = (data.get("time") or {}).get("iso")
        if isinstance(iso_time, str):
            try:
                observed_at = datetime.fromisoformat(iso_time.replace("Z", "+00:00")).replace(
                    tzinfo=None
                )
            except ValueError:
                pass

        slug = _nearest_slug(lat, lon) or slug_hint
        iaqi = data.get("iaqi") or {}
        records: list[PollutionRecord] = []
        for key, pollutant in IAQI_MAP.items():
            value = (iaqi.get(key) or {}).get("v")
            if value is None or float(value) < 0:
                continue
            records.append(
                PollutionRecord(
                    station_slug=slug,
                    pollutant=pollutant,
                    value=float(value),
                    unit=UNIT_BY_POLLUTANT[pollutant],
                    observed_at=observed_at,
                    source_code="waqi",
                    quality_flag="raw",
                )
            )
        return records
