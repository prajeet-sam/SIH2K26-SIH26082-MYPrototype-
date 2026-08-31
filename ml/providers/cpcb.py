"""CPCB CAAQMS ingestion via the data.gov.in real-time air-quality resource.

Requires DATA_GOV_IN_API_KEY (and optionally CPCB_RESOURCE_ID). Returns raw,
station-matched records; timestamps arrive in IST and are stored naive-UTC.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any

import httpx

from ml.config.settings import Settings
from ml.providers.base import AirQualityProvider, PollutionRecord, ProviderError, StationRef
from ml.storage.station_catalog import STATION_CATALOG

API_URL = "https://api.data.gov.in/resource"
DEFAULT_RESOURCE_ID = "3b01bcb8-0bf4-419e-a465-0d02a72eb3d9"
PAGE_SIZE = 1000

POLLUTANT_MAP = {
    "PM2.5": "pm25",
    "PM10": "pm10",
    "NO2": "no2",
    "SO2": "so2",
    "CO": "co",
    "OZONE": "o3",
    "NH3": "nh3",
}

_IST_OFFSET = timedelta(hours=5, minutes=30)
_norm_re = re.compile(r"[^a-z0-9]+")


def _norm(text: str) -> str:
    return _norm_re.sub("", text.lower())


def build_station_index() -> list[tuple[str, str, float, float]]:
    return [(s["slug"], _norm(s["name"]), s["latitude"], s["longitude"]) for s in STATION_CATALOG]


def match_station_slug(
    raw_name: str, city: str | None, lat: float | None, lon: float | None
) -> str | None:
    """Match a provider station label to a canonical slug by name tokens, then proximity."""
    index = build_station_index()
    norm = _norm(raw_name)
    best: tuple[int, str] | None = None
    for slug, norm_name, _, _ in index:
        if norm_name and (norm_name in norm or norm.startswith(norm_name)):
            score = abs(len(norm) - len(norm_name))
            if best is None or score < best[0]:
                best = (score, slug)
    if best is not None:
        return best[1]
    if lat is None or lon is None:
        return None
    near: tuple[float, str] | None = None
    for slug, _, slat, slon in index:
        d = ((slat - lat) ** 2 + ((slon - lon) * 0.87) ** 2) ** 0.5
        if d < 0.05 and (near is None or d < near[0]):
            near = (d, slug)
    return near[1] if near else None


def parse_last_updated(raw: str) -> datetime | None:
    for fmt in ("%d-%m-%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y %H:%M:%S"):
        try:
            return datetime.strptime(raw.strip(), fmt) - _IST_OFFSET
        except ValueError:
            continue
    return None


class CpcbProvider(AirQualityProvider):
    code = "cpcb"
    display_name = "CPCB CAAQMS (via data.gov.in)"
    requires_key = True

    def __init__(self, settings: Settings, client: httpx.Client | None = None):
        self._settings = settings
        self._client = client

    def is_available(self) -> bool:
        return bool(self._settings.data_gov_in_api_key)

    def fetch_window(
        self, stations: Sequence[StationRef], start_utc: datetime, end_utc: datetime
    ) -> list[PollutionRecord]:
        # CPCB resource is region-wide; we filter by station match after fetch.
        allowed_slugs = {s.slug for s in stations}
        records: list[PollutionRecord] = []
        client = self._client or httpx.Client(timeout=self._settings.http_timeout_seconds)
        try:
            offset = 0
            while True:
                params: dict[str, Any] = {
                    "api-key": self._settings.data_gov_in_api_key,
                    "format": "json",
                    "limit": PAGE_SIZE,
                    "offset": offset,
                }
                try:
                    resp = client.get(
                        f"{API_URL}/{self._settings.cpcb_resource_id or DEFAULT_RESOURCE_ID}",
                        params=params,
                    )
                    resp.raise_for_status()
                    payload = resp.json()
                except httpx.HTTPError as exc:
                    raise ProviderError(f"cpcb request failed: {exc}") from exc

                rows = payload.get("records") or []
                records.extend(self._parse_records(rows, allowed_slugs))
                total = int(payload.get("total") or 0)
                offset += PAGE_SIZE
                if not rows or offset >= total:
                    break
        finally:
            if self._client is None:
                client.close()
        return [r for r in records if start_utc <= r.observed_at <= end_utc]

    @staticmethod
    def _parse_records(rows: list[dict], allowed_slugs: set[str]) -> list[PollutionRecord]:
        records: list[PollutionRecord] = []
        for row in rows:
            pollutant = POLLUTANT_MAP.get(str(row.get("pollutant_id", "")).strip().upper())
            if pollutant is None:
                continue
            try:
                value = float(row.get("pollutant_avg"))
            except (TypeError, ValueError):
                continue
            if value < 0:
                continue
            observed_at = parse_last_updated(
                str(row.get("last_update") or row.get("last_updated") or "")
            )
            if observed_at is None:
                continue
            raw_station = str(row.get("station", "")).strip()
            slug = match_station_slug(raw_station, row.get("city"), None, None)
            if slug is None or slug not in allowed_slugs:
                continue
            unit = "mg/m3" if pollutant == "co" else "ug/m3"
            records.append(
                PollutionRecord(
                    station_slug=slug,
                    pollutant=pollutant,
                    value=value / 1000.0 if pollutant == "co" else value,
                    unit=unit,
                    observed_at=observed_at,
                    source_code="cpcb",
                    quality_flag="raw",
                )
            )
        return records
