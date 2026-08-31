from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from ml.features.builder import FeatureVector, build_feature_vector, dataset_hash
from ml.preprocessing.aqi import categorize, color_for, overall_aqi, sub_index
from ml.preprocessing.cleaning import clean_pollution, clean_weather
from ml.providers.base import PollutionRecord, WeatherRecord

T0 = datetime(2026, 1, 10, 6, 0)


def pol(
    value: float, pollutant: str = "pm25", hours_ago: int = 0, source: str = "open-meteo-air"
) -> PollutionRecord:
    return PollutionRecord(
        station_slug="anand-vihar",
        pollutant=pollutant,
        value=value,
        unit="mg/m3" if pollutant == "co" else "ug/m3",
        observed_at=T0 - timedelta(hours=hours_ago),
        source_code=source,
    )


def test_sub_index_breakpoints():
    assert sub_index("pm25", 29) == 48
    assert sub_index("pm25", 30) == 50
    assert sub_index("pm25", 60) == 100
    assert sub_index("pm25", 61) == 103
    assert sub_index("pm25", 500) == 500
    assert sub_index("pm25", -1) is None


def test_overall_aqi_dominant_pollutant():
    aqi, dom = overall_aqi({"pm25": 95.0, "no2": 30.0})
    assert dom == "pm25"
    assert aqi == 217
    assert categorize(aqi) == "Poor"
    assert color_for(420) == "#7d2181"


def test_cleaning_drops_future_and_range_but_flags_high():
    records = [
        pol(120.0),
        pol(5000.0),  # range drop
        pol(80.0, hours_ago=-5),  # future drop
    ]
    kept, report = clean_pollution(records, now_utc=T0)
    assert report.seen == 3
    assert len(kept) == 1
    assert report.dropped_range == 1
    assert report.dropped_future == 1
    # open-meteo sources get relabelled interpolated
    assert kept[0].quality_flag == "interpolated"


def test_cleaning_weather_ranges():
    good = WeatherRecord(
        station_slug="anand-vihar",
        observed_at=T0,
        temperature_c=18,
        relative_humidity_pct=70,
        wind_speed_ms=3,
        precipitation_mm=0,
        source_code="open-meteo",
    )
    bad_rh = good.model_copy(update={"relative_humidity_pct": 140})
    kept, report = clean_weather([good, bad_rh], now_utc=T0)
    assert len(kept) == 1 and report.dropped_range == 1


def test_feature_vector_is_causal_and_complete():
    pm_series = [(T0 - timedelta(hours=h), 60 + h * 2) for h in range(0, 40)]
    wx = [
        WeatherRecord(
            station_slug="anand-vihar",
            observed_at=T0 - timedelta(hours=h),
            temperature_c=20.0,
            relative_humidity_pct=60.0,
            wind_speed_ms=1.0 if h % 3 else 4.0,
            wind_direction_deg=300.0,
            precipitation_mm=0.5 if h in (2, 3) else 0.0,
            pressure_hpa=1010.0,
            source_code="demo-wx",
        )
        for h in range(0, 26)
    ]
    fv = build_feature_vector("anand-vihar", T0, pm_series, wx)
    assert fv.pm25_lag1 == pytest.approx(62.0)
    assert fv.pm25_lag24 == pytest.approx(108.0)
    assert fv.pm25_mean_24h > 0
    assert fv.ws_ms == pytest.approx(4.0)
    assert fv.precip_mm_6h == pytest.approx(1.0)
    assert 0 <= fv.stagnation_24h <= 1
    assert abs(fv.hour_sin) <= 1 and abs(fv.month_cos) <= 1
    payload = fv.to_payload()
    assert '"pm25_lag1"' in payload


def test_no_future_leakage_in_features():
    # A value recorded AFTER feature_time must never appear in any lag.
    pm_series = [(T0 + timedelta(hours=1), 999.0), (T0 - timedelta(hours=1), 42.0)]
    fv = build_feature_vector("anand-vihar", T0, pm_series, [])
    assert fv.pm25_lag1 == pytest.approx(42.0)


def test_dataset_hash_stable_and_sensitive():
    a = FeatureVector(station_slug="s", feature_time=T0, pm25_lag1=10)
    b = FeatureVector(station_slug="s", feature_time=T0, pm25_lag1=11)
    assert dataset_hash([a]) == dataset_hash([a])
    assert dataset_hash([a]) != dataset_hash([b])
