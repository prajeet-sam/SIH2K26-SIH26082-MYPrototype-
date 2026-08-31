from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import datetime, timedelta

from ml.providers.base import (
    AirQualityProvider,
    PollutionRecord,
    ProviderUnavailable,
    StationRef,
    WeatherProvider,
    WeatherRecord,
)

CITY_FACTOR: dict[str, float] = {
    "Delhi": 1.0,
    "Noida": 0.96,
    "Greater Noida": 0.9,
    "Ghaziabad": 1.03,
    "Gurugram": 0.93,
    "Faridabad": 0.99,
}

HOTSPOT_FACTOR: dict[str, float] = {
    "anand-vihar": 1.42,
    "wazirpur": 1.38,
    "bawana": 1.33,
    "mundka": 1.36,
    "jahangirpuri": 1.27,
    "narela": 1.22,
    "ito": 1.18,
    "indirapuram": 1.16,
    "burari-crossing": 1.15,
    "loni": 1.14,
    "chandni-chowk": 1.14,
    "lodhi-road": 0.82,
    "aya-nagar": 0.85,
    "gwal-pahari": 0.78,
    "teri-gram": 0.8,
}


def _seed(*parts: object) -> int:
    text = ":".join(str(p) for p in parts)
    h = 2166136261
    for ch in text:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def _rand01(seed: int, i: int = 0) -> float:
    a = (seed ^ (i * 0x9E3779B9)) & 0xFFFFFFFF
    a = (a + 0x6D2B79F5) & 0xFFFFFFFF
    t = a
    t = ((t ^ (t >> 15)) * (1 | t)) & 0xFFFFFFFF
    t = (t + ((t ^ (t >> 7)) * (61 | t))) ^ t
    return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296


def month_factor(month: int) -> float:
    return {
        0: 2.1,
        1: 2.1,
        2: 1.4,
        3: 1.1,
        5: 0.62,
        6: 0.62,
        7: 0.62,
        8: 0.68,
        9: 1.35,
        10: 2.3,
        11: 2.2,
    }.get(month, 0.9)


def diurnal_factor(hour_ist: float) -> float:
    morning = math.exp(-((hour_ist - 8.5) ** 2) / 6)
    night = math.exp(-((hour_ist - 22.5) ** 2) / 10)
    dip = math.exp(-((hour_ist - 15) ** 2) / 8)
    return 1 + 0.38 * morning + 0.42 * night - 0.3 * dip


def ist_hour(dt_utc: datetime) -> float:
    shifted = dt_utc + timedelta(hours=5, minutes=30)
    return shifted.hour + shifted.minute / 60


class DemoProviderMixin:
    def sample(
        self, station: StationRef, dt: datetime
    ) -> tuple[dict[str, float], dict[str, float]]:
        hour_index = int(dt.replace(minute=0, second=0, microsecond=0).timestamp() // 3600)
        hod = ist_hour(dt)

        def rng_w(i):
            return _rand01(_seed(station.slug, "w", hour_index), i)

        def rng_p(i):
            return _rand01(_seed(station.slug, "p", hour_index), i)

        city_factor = CITY_FACTOR.get(station.city, 0.9)
        hotspot = HOTSPOT_FACTOR.get(station.slug, 1.0)
        mf = month_factor(dt.month)

        rain_recent = sum(
            1 for k in range(1, 9) if rng_w(50 + k) < 0.07 and dt.month in (6, 7, 8, 9)
        )
        calm_night = 0.55 if (hod >= 22 or hod <= 6) else 1.0
        gusty_day = 1.35 if 12 <= hod <= 17 else 1.0
        ws = max(0.3, 2.9 * calm_night * gusty_day * mf**0.25 * (0.6 + rng_w(1) * 0.9))
        temp = (
            31
            - 4 * mf**0.3
            + 6.5 * math.sin(((hod - 14) / 24) * 2 * math.pi)
            + (rng_w(2) - 0.5) * 3
        )
        rh = min(98.0, max(22.0, 74 - (temp - 29) * 3.2 + (rng_w(3) - 0.5) * 14))
        rain = 2 + rng_w(4) * 14 if (rng_w(5) < 0.07 and dt.month in (6, 7, 8, 9)) else 0.0
        wdir = (295 + 70 * math.sin(hour_index / 41) + (rng_w(6) - 0.5) * 50 + 360) % 360
        pressure = 1006 + 3 * math.sin(hour_index / 120) + (rng_w(7) - 0.5) * 4

        washout = 1 - 0.035 * min(rain_recent, 8)
        ventilation = max(0.45, 1.45 - 0.22 * ws)
        moisture = 0.9 + ((rh - 55) / 100) * 0.35
        traffic = 1 + 0.3 * (math.exp(-((hod - 9) ** 2) / 4) + math.exp(-((hod - 20) ** 2) / 5))

        base = (
            52 * city_factor * hotspot * mf * diurnal_factor(hod) * ventilation * moisture * washout
        )
        pm25 = max(6.0, base * (0.85 + rng_p(1) * 0.3))
        pm10 = max(12.0, pm25 * (1.55 + rng_p(2) * 0.4) + 12)
        no2 = max(
            5.0, 34 * city_factor * hotspot * traffic * (1.25 - 0.09 * ws) * (0.8 + rng_p(3) * 0.4)
        )
        so2 = max(2.0, 11 * city_factor * hotspot * (0.7 + rng_p(4) * 0.6))
        co = max(0.2, 1.05 * traffic * city_factor * (0.7 + rng_p(5) * 0.6))
        photo = max(0.0, math.sin(((hod - 13) / 9.5) * math.pi))
        o3 = max(6.0, (18 + 62 * photo) * (0.85 + rng_p(6) * 0.3))

        weather = {
            "temperature_c": round(temp, 1),
            "relative_humidity_pct": round(rh),
            "wind_speed_ms": round(ws, 1),
            "wind_direction_deg": round(wdir),
            "precipitation_mm": round(rain, 1),
            "pressure_hpa": round(pressure, 1),
        }
        pollution = {
            "pm25": round(pm25, 1),
            "pm10": round(pm10, 1),
            "no2": round(no2, 1),
            "so2": round(so2, 1),
            "co": round(co, 2),
            "o3": round(o3, 1),
        }
        return weather, pollution


class DemoAirQualityProvider(AirQualityProvider, DemoProviderMixin):
    code = "demo"
    display_name = "Bundled synthetic dataset (labelled demo)"
    requires_key = False

    def is_available(self) -> bool:
        return True

    def fetch_window(
        self, stations: Sequence[StationRef], start_utc: datetime, end_utc: datetime
    ) -> list[PollutionRecord]:
        records: list[PollutionRecord] = []
        for station in stations:
            t = start_utc.replace(minute=0, second=0, microsecond=0)
            while t <= end_utc:
                _, pollution = self.sample(station, t)
                for pollutant, value in pollution.items():
                    records.append(
                        PollutionRecord(
                            station_slug=station.slug,
                            pollutant=pollutant,
                            value=value,
                            unit="mg/m3" if pollutant == "co" else "ug/m3",
                            observed_at=t,
                            source_code=self.code,
                        )
                    )
                t += timedelta(hours=1)
        return records


class DemoWeatherProvider(WeatherProvider, DemoProviderMixin):
    code = "demo-wx"
    display_name = "Bundled synthetic weather (labelled demo)"
    requires_key = False

    def is_available(self) -> bool:
        return True

    def fetch_window(
        self, stations: Sequence[StationRef], start_utc: datetime, end_utc: datetime
    ) -> list[WeatherRecord]:
        records: list[WeatherRecord] = []
        for station in stations:
            t = start_utc.replace(minute=0, second=0, microsecond=0)
            while t <= end_utc:
                weather, _ = self.sample(station, t)
                records.append(
                    WeatherRecord(
                        station_slug=station.slug, observed_at=t, source_code=self.code, **weather
                    )
                )
                t += timedelta(hours=1)
        return records


def raise_unavailable(name: str) -> None:
    raise ProviderUnavailable(
        f"{name} credentials not configured — set the required environment variable to enable it."
    )
