from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from starlette.testclient import TestClient

from api.main import app
from ml.forecasting import features as feat
from ml.forecasting.models import (
    MLAUnavailableError,
    PersistenceBaseline,
    RidgeQuantileForecaster,
)

client = TestClient(app)


def _series(n: int = 300) -> list[tuple[datetime, float]]:
    start = datetime(2026, 1, 1, 0)
    out = []
    val = 100.0
    for i in range(n):
        ts = start + timedelta(hours=i)
        out.append((ts, val))
        val = max(5.0, val + (i % 5) - 2)
    return out


def test_feature_no_leakage():
    """Features at time t must not use observations after t."""
    series = _series()
    weather: dict[datetime, object] = {}
    t = series[50][0]
    row = feat.feature_row(t, series, weather)
    # lag1 at time t equals value exactly 1h before t.
    expected = series[49][1]
    assert row["target_lag1"] is not None
    assert abs(row["target_lag1"] - expected) < 1e-9
    # Construct a version of the series with future data removed before t and
    # confirm the same feature value (independence from the future).
    feat_before_future = feat.feature_row(t, [s for s in series if s[0] <= t], weather)
    assert row["target_lag1"] == feat_before_future["target_lag1"]
    assert row["target_mean_6h"] == feat_before_future["target_mean_6h"]


def test_feature_column_order_stable():
    expected = (
        "target_lag1",
        "target_lag3",
        "target_lag6",
        "target_lag12",
        "target_lag24",
        "target_mean_6h",
        "target_mean_24h",
        "target_std_24h",
        "target_slope_3h",
        "temp_c",
        "rh_pct",
        "ws_ms",
        "wd_sin",
        "wd_cos",
        "precip_mm_6h",
        "pressure_hpa",
        "stagnation_24h",
        "rain_hours_24h",
        "hour_sin",
        "hour_cos",
        "month_sin",
        "month_cos",
    )
    assert feat.FEATURE_COLUMNS == expected


def test_persistence_baseline_shape_and_widening():
    times = [datetime(2026, 1, 1, 0) + timedelta(hours=h) for h in range(1, 5)]
    base = PersistenceBaseline(180.0, [160, 170, 175, 180, 190])
    points = base.predict(times)
    assert len(points) == 4
    for p in points:
        assert p.p10 <= p.p50 <= p.p90
        assert p.p50 == 180.0
    # Uncertainty should widen with horizon.
    assert (points[3].p90 - points[3].p10) >= (points[0].p90 - points[0].p10)


def test_ridge_forecaster_fit_predict_or_skip():
    """If sklearn is unavailable, the training path must degrade (not crash)."""
    series = _series()
    X, y = [], []
    for t, v in series[120:]:
        row = feat.feature_row(t, series, {})
        if row.get("target_lag1") is not None:
            X.append(row)
            y.append(v)
    model = RidgeQuantileForecaster()
    try:
        model.fit(X, y)
    except MLAUnavailableError:
        pytest.skip("native ML stack unavailable in this runtime")
    preds = model.predict(X[:5])
    assert len(preds) == 5
    for p10, p50, p90 in preds:
        assert 0 <= p10 <= p50 <= p90
    assert model.feature_importances and len(model.feature_importances) == len(
        model.feature_columns
    )


def test_forecast_route_real_points():
    r = client.get("/api/forecast/anand-vihar?targets=pm25&horizons=24")
    assert r.status_code == 200
    data = r.json()
    assert len(data["points"]) == 24
    p = data["points"][0]
    assert p["confidence"] in ("low", "moderate", "high")
    assert p["p50"] is not None and p["p50"] >= 0
    assert p["targetTime"]  # non-empty
    if p["p10"] is not None and p["p90"] is not None:
        assert p["p10"] <= p["p90"]


def test_forecast_weather_route():
    r = client.get("/api/forecast/weather?station_id=anand-vihar&ahead_hours=24")
    assert r.status_code == 200
    # Weather forecast is optional network data; accept empty or populated.
    assert isinstance(r.json(), list)


def test_explain_route_honesty():
    r = client.get("/api/forecast/explain/anand-vihar?target=pm25")
    assert r.status_code == 200
    data = r.json()
    assert data["stationId"] == "anand-vihar"
    assert "narrative" in data and "disclaimer" in data
    assert data["confidence"] in ("low", "moderate", "high")


def test_model_performance_is_honest():
    r = client.get("/api/model/performance?target=pm25")
    assert r.status_code == 200
    rows = r.json()
    assert isinstance(rows, list)


def test_correlations_shape():
    r = client.get("/api/research/correlations?station_id=anand-vihar&days=30")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data["rows"], list)
    assert isinstance(data["cols"], list)
    assert isinstance(data["values"], list)


def test_aqi_forecast_route():
    """The homepage requests `targets=aqi`; it must resolve to a real forecast."""
    r = client.get("/api/forecast/anand-vihar?targets=aqi&horizons=24")
    assert r.status_code == 200
    data = r.json()
    assert data["target"] == "aqi"
    assert len(data["points"]) == 24
    for p in data["points"]:
        assert p["p50"] is not None and p["p50"] >= 0
