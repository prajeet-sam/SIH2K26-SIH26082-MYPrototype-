from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from ml.config.settings import Settings
from ml.providers.base import StationRef
from ml.providers.demo import DemoAirQualityProvider, DemoWeatherProvider
from ml.providers.open_meteo import OpenMeteoWeatherProvider
from ml.providers.registry import build_air_quality_providers, build_weather_providers
from ml.storage.db import init_schema, make_engine, make_session_factory
from ml.storage.models import PollutionObservation, WeatherObservation
from ml.storage.upsert import upsert_rows


@pytest.fixture()
def engine(tmp_path):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'test.db'}")
    eng = make_engine(settings)
    init_schema(eng)
    return eng


@pytest.fixture()
def factory(engine) -> sessionmaker:
    return make_session_factory(engine)


@pytest.fixture()
def seeded_factory(engine, factory):
    from scripts.seed_stations import seed

    seed(engine)
    return factory


STATION_REF = [
    StationRef(
        slug="anand-vihar", name="Anand Vihar", city="Delhi", latitude=28.6469, longitude=77.3162
    )
]


def test_seed_is_idempotent_and_complete(seeded_factory, engine):
    from sqlalchemy import func, select

    from ml.storage.models import AlertRule, DataSource, Station

    with seeded_factory() as s:
        assert s.execute(select(func.count()).select_from(Station)).scalar_one() == 54
        assert s.execute(select(func.count()).select_from(DataSource)).scalar_one() == 7
        assert s.execute(select(func.count()).select_from(AlertRule)).scalar_one() == 2

    from scripts.seed_stations import seed as run_seed

    counts = run_seed(engine)
    assert counts["stations"] >= 54


def test_pollution_obs_upsert_conflict(factory, seeded_factory):
    t0 = datetime(2026, 1, 10, 6, 0)
    row = dict(
        station_slug="anand-vihar",
        pollutant="pm25",
        value=180.5,
        unit="ug/m3",
        observed_at=t0,
        source_id=4,
        quality_flag="cleaned",
    )
    with factory() as s:
        ins, upd = upsert_rows(
            s,
            PollutionObservation,
            [row],
            ["station_slug", "pollutant", "observed_at", "source_id"],
            ["value", "unit", "quality_flag"],
        )
        assert (ins, upd) == (1, 0)

        row2 = {**row, "value": 210.0}
        ins, upd = upsert_rows(
            s,
            PollutionObservation,
            [row2],
            ["station_slug", "pollutant", "observed_at", "source_id"],
            ["value", "unit", "quality_flag"],
        )
        assert (ins, upd) == (0, 1)
        got = s.query(PollutionObservation).one()
        assert got.value == 210.0


def test_check_constraints_reject_bad_values(factory, seeded_factory):
    bad = PollutionObservation(
        station_slug="anand-vihar",
        pollutant="pm25",
        value=-5,
        observed_at=datetime(2026, 1, 10, 6),
        source_id=4,
    )
    with factory() as s:
        s.add(bad)
        with pytest.raises(IntegrityError):
            s.commit()


def test_fk_blocks_unknown_station(factory, seeded_factory):
    orphan = WeatherObservation(
        station_slug="not-a-station", observed_at=datetime(2026, 1, 10, 6), source_id=5
    )
    with factory() as s:
        s.add(orphan)
        with pytest.raises(IntegrityError):
            s.commit()


def test_open_meteo_parse_payload():
    payload = {
        "hourly": {
            "time": ["2026-01-10T05:00", "2026-01-10T06:00"],
            "temperature_2m": [12.3, None],
            "relative_humidity_2m": [71, 74],
            "wind_speed_10m": [2.1, 3.4],
            "wind_direction_10m": [290, 300],
            "precipitation": [0.0, 0.4],
        }
    }
    recs = OpenMeteoWeatherProvider.parse_payload(STATION_REF, payload)
    assert len(recs) == 2
    first = recs[0]
    assert first.station_slug == "anand-vihar"
    assert first.temperature_c == 12.3
    assert first.wind_speed_ms == 2.1
    assert first.observed_at.tzinfo is None
    assert recs[1].temperature_c is None
    assert recs[1].precipitation_mm == 0.4


def test_demo_producers_hourly_window():
    start = datetime(2026, 1, 10, 0, 0)
    end = start + timedelta(hours=23)
    pol = DemoAirQualityProvider().fetch_window(STATION_REF, start, end)
    wx = DemoWeatherProvider().fetch_window(STATION_REF, start, end)
    assert len(pol) == 24 * 6
    assert len(wx) == 24
    pollutants = {r.pollutant for r in pol}
    assert pollutants == {"pm25", "pm10", "no2", "so2", "co", "o3"}
    co_units = {r.unit for r in pol if r.pollutant == "co"}
    assert co_units == {"mg/m3"}
    assert all(0 <= r.relative_humidity_pct <= 100 and r.wind_speed_ms >= 0 for r in wx)


def test_registry_respects_keys_and_demo(tmp_path):
    demo_settings = Settings(database_url=f"sqlite:///{tmp_path / 'a.db'}", demo_mode=True)
    assert isinstance(build_air_quality_providers(demo_settings)[0], DemoAirQualityProvider)
    assert isinstance(build_weather_providers(demo_settings)[0], DemoWeatherProvider)

    keyless = Settings(
        database_url=f"sqlite:///{tmp_path / 'b.db'}",
        demo_mode=False,
        data_gov_in_api_key="",
        openaq_api_key="",
    )
    aq_codes = [p.code for p in build_air_quality_providers(keyless)]
    assert aq_codes == ["open-meteo-air"]
    wx_codes = [p.code for p in build_weather_providers(keyless)]
    assert wx_codes == ["open-meteo"]
