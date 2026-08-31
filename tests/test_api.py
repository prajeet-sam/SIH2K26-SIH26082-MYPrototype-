from __future__ import annotations

from starlette.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_stations_schema():
    r = client.get("/api/stations")
    assert r.status_code == 200
    stations = r.json()
    assert len(stations) >= 50
    s0 = stations[0]
    for key in (
        "id",
        "slug",
        "name",
        "city",
        "latitude",
        "longitude",
        "pollutantsAvailable",
        "isActive",
    ):
        assert key in s0, f"missing key {key}"
    assert s0["slug"] == s0["id"]
    assert isinstance(s0["pollutantsAvailable"], list)


def test_current_conditions_schema():
    r = client.get("/api/air-quality/current")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 40
    c0 = data[0]
    for key in (
        "stationId",
        "slug",
        "aqi",
        "category",
        "dominantPollutant",
        "pollutants",
        "weather",
        "freshnessMinutes",
        "trend24hAqi",
    ):
        assert key in c0, f"missing key {key}"
    assert c0["aqi"] >= 0
    assert isinstance(c0["trend24hAqi"], list) and len(c0["trend24hAqi"]) == 25
    assert isinstance(c0["weather"], dict)
    assert isinstance(c0["pollutants"], dict)


def test_observation_history_schema():
    r = client.get("/api/air-quality/history?station_id=anand-vihar&tail_hours=72")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    p0 = data[0]
    for key in ("time", "aqi", "pollutants", "qualityFlag"):
        assert key in p0, f"missing key {key}"
    assert isinstance(p0["pollutants"], dict)


def test_weather_history_schema():
    r = client.get("/api/weather/history?station_id=anand-vihar&tail_hours=168")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    if data:
        w0 = data[0]
        for key in ("time", "temperatureC", "relativeHumidityPct", "windSpeedMs"):
            assert key in w0, f"missing key {key}"


def test_station_availability_schema():
    r = client.get("/api/stations/anand-vihar/availability")
    assert r.status_code == 200
    data = r.json()
    assert data["slug"] == "anand-vihar"
    assert isinstance(data["matrix"], dict)


def test_alerts_and_dq_empty_shapes():
    a = client.get("/api/alerts")
    dq = client.get("/api/data-quality/status")
    assert a.status_code == 200
    assert dq.status_code == 200
    assert isinstance(a.json(), list)
    assert isinstance(dq.json(), list)


def test_forecast_stub_schema():
    r = client.get("/api/forecast/anand-vihar?targets=pm25&horizons=24")
    assert r.status_code == 200
    data = r.json()
    assert data["stationId"] == "anand-vihar"
    assert data["target"] == "pm25"
    assert len(data["points"]) == 24
    p = data["points"][0]
    assert "targetTime" in p and "horizonHours" in p and "confidence" in p


def test_explain_stub_schema():
    r = client.get("/api/forecast/explain/anand-vihar?target=pm25&horizon_hours=24")
    assert r.status_code == 200
    data = r.json()
    assert data["stationId"] == "anand-vihar"
    assert "narrative" in data and "contributions" in data


def test_model_performance_stub():
    r = client.get("/api/model/performance?target=pm25")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_correlations_stub():
    r = client.get("/api/research/correlations?station_id=anand-vihar&days=30")
    assert r.status_code == 200
    assert "rows" in r.json() and "values" in r.json()
