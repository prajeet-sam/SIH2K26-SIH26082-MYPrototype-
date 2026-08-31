from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

QualityFlag = Literal["raw", "cleaned", "interpolated", "suspect"]


class ProviderError(Exception):
    pass


class ProviderUnavailable(ProviderError):
    pass


class StationRef(BaseModel):
    slug: str
    name: str
    city: str
    latitude: float
    longitude: float


class PollutionRecord(BaseModel):
    station_slug: str
    pollutant: Literal["pm25", "pm10", "no2", "so2", "co", "o3", "nh3"]
    value: float = Field(ge=0)
    unit: str = "ug/m3"
    observed_at: datetime
    source_code: str
    quality_flag: QualityFlag = "cleaned"

    @field_validator("observed_at")
    @classmethod
    def _naive_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is not None:
            v = v.replace(tzinfo=None)
        return v


class WeatherRecord(BaseModel):
    station_slug: str
    observed_at: datetime
    temperature_c: float | None = None
    relative_humidity_pct: float | None = Field(default=None, ge=0, le=100)
    wind_speed_ms: float | None = Field(default=None, ge=0)
    wind_direction_deg: float | None = Field(default=None, ge=0, le=360)
    wind_gust_ms: float | None = Field(default=None, ge=0)
    precipitation_mm: float | None = Field(default=None, ge=0)
    pressure_hpa: float | None = None
    source_code: str
    quality_flag: QualityFlag = "cleaned"

    @field_validator("observed_at")
    @classmethod
    def _naive_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is not None:
            v = v.replace(tzinfo=None)
        return v


class AirQualityProvider(ABC):
    code: str
    display_name: str
    requires_key: bool = False

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def fetch_window(
        self, stations: Sequence[StationRef], start_utc: datetime, end_utc: datetime
    ) -> list[PollutionRecord]: ...


class WeatherProvider(ABC):
    code: str
    display_name: str
    requires_key: bool = False

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def fetch_window(
        self, stations: Sequence[StationRef], start_utc: datetime, end_utc: datetime
    ) -> list[WeatherRecord]: ...
