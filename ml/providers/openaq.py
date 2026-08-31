"""OpenAQ v3 adapter (latest measurements per location near each catalog station).

Requires OPENAQ_API_KEY. Two-step per matched location: location detail gives
sensor->parameter mapping; /latest gives current values.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta

import httpx

from ml.config.settings import Settings
from ml.providers.base import AirQualityProvider, PollutionRecord, ProviderError, StationRef
from ml.providers.cpcb import _norm, match_station_slug

API_URL = "https://api.openaq.org/v3"
RADIUS_M = 8000

POLLUTANT_MAP = {
    "pm25": "pm25",
    "pm10": "pm10",
    "no2": "no2",
    "so2": "so2",
    "co": "co",
    "o3": "o3",
    "nh3": "nh3",
}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    from math import asin, cos, radians, sin

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * 6371.0 * asin(a**0.5)


class OpenAqProvider(AirQualityProvider):
    code = "openaq"
    display_name = "OpenAQ v3"
    requires_key = True

    def __init__(self, settings: Settings, client: httpx.Client | None = None):
        self._settings = settings
        self._client = client or httpx.Client(
            timeout=settings.http_timeout_seconds,
            headers={"X-API-Key": settings.openaq_api_key},
        )

    def is_available(self) -> bool:
        return bool(self._settings.openaq_api_key)

    def fetch_window(
        self, stations: Sequence[StationRef], start_utc: datetime, end_utc: datetime
    ) -> list[PollutionRecord]:
        records: list[PollutionRecord] = []
        client = self._client or httpx.Client(timeout=self._settings.http_timeout_seconds)
        try:
            for station in stations:
                records.extend(self._fetch_station(client, station))
        finally:
            if self._client is None:
                client.close()
        cutoff = start_utc - timedelta(minutes=180)
        return [r for r in records if r.observed_at >= cutoff and r.observed_at <= end_utc]

    def _fetch_station(self, client: httpx.Client, station: StationRef) -> list[PollutionRecord]:
        try:
            resp = client.get(
                f"{API_URL}/locations",
                params={
                    "coordinates": f"{station.latitude},{station.longitude}",
                    "radius": RADIUS_M,
                    "limit": 10,
                },
            )
            resp.raise_for_status()
            locations = resp.json().get("results", [])
        except httpx.HTTPError as exc:
            raise ProviderError(f"openaq locations request failed: {exc}") from exc

        target = self._match_location(locations, station.name)
        if target is None:
            return []
        return self._fetch_latest(client, target)

    @staticmethod
    def _match_location(locations: list[dict], name: str) -> dict | None:
        norm = _norm(name)
        best: tuple[float, dict] | None = None
        for loc in locations:
            loc_norm = _norm(str(loc.get("name", "")))
            if not loc_norm:
                continue
            score = (
                0.0
                if loc_norm == norm
                else 1.0
                if norm in loc_norm or loc_norm.startswith(norm)
                else 2.0
            )
            if score >= 2.0 and best is None:
                best = (score + len(loc_norm) / 1000.0, loc)
            elif score < 2.0 and (best is None or score + len(loc_norm) / 1000.0 < best[0]):
                best = (score + len(loc_norm) / 1000.0, loc)
        return best[1] if best else None

    def _fetch_latest(self, client: httpx.Client, location: dict) -> list[PollutionRecord]:
        loc_id = location.get("id")
        try:
            detail = client.get(f"{API_URL}/locations/{loc_id}").json()
            latest = client.get(f"{API_URL}/locations/{loc_id}/latest").json()
        except httpx.HTTPError as exc:
            raise ProviderError(f"openaq latest request failed: {exc}") from exc

        sensor_params: dict[int, tuple[str, str]] = {}
        for sensor in detail.get("results", [{}])[0].get("sensors", []):
            param = sensor.get("parameter", {})
            code = POLLUTANT_MAP.get(str(param.get("name", "")).lower())
            if code:
                sensor_params[sensor["id"]] = (code, str(param.get("units", "ug/m3")))

        records: list[PollutionRecord] = []
        slug_hint = str(location.get("name", ""))
        slug = match_station_slug(
            slug_hint,
            None,
            location.get("coordinates", {}).get("latitude"),
            location.get("coordinates", {}).get("longitude"),
        )
        if slug is None:
            return []
        for row in latest.get("results", []):
            mapped = sensor_params.get(row.get("sensorsId"))
            if mapped is None:
                continue
            pollutant, unit = mapped
            value_raw = row.get("value")
            if value_raw is None or float(value_raw) < 0:
                continue
            utc_raw = (row.get("datetime") or {}).get("utc") or ""
            try:
                observed_at = datetime.fromisoformat(utc_raw.replace("Z", "+00:00")).replace(
                    tzinfo=None
                )
            except ValueError:
                continue
            records.append(
                PollutionRecord(
                    station_slug=slug,
                    pollutant=pollutant,
                    value=float(value_raw),
                    unit=unit,
                    observed_at=observed_at,
                    source_code="openaq",
                    quality_flag="raw",
                )
            )
        return records
