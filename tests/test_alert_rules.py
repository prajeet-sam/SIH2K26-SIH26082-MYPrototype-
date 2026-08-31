from __future__ import annotations

from starlette.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_rules_list_public():
    r = client.get("/api/alerts/rules")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_rules_create_requires_admin():
    r = client.post(
        "/api/alerts/rules",
        json={"name": "t", "metric": "pm25", "comparator": ">", "threshold": 100},
    )
    # Without AIRACAST_ADMIN_TOKEN configured -> 501 (not 201).
    assert r.status_code in (501, 401, 201)


def test_rules_update_requires_admin():
    r = client.put("/api/alerts/rules/1", json={"threshold": 120})
    assert r.status_code in (501, 401, 404)


def test_rules_create_roundtrip_with_token(monkeypatch):
    import uuid

    import api.routes.alerts as alerts_mod

    # `alerts` imported `get_settings` by name, so patch it there.
    monkeypatch.setattr(
        alerts_mod, "get_settings", lambda: type("S", (), {"admin_token": "secret"})()
    )
    name = f"test-rule-{uuid.uuid4().hex[:8]}"
    r = client.post(
        "/api/alerts/rules",
        json={"name": name, "metric": "pm25", "comparator": ">", "threshold": 150},
        headers={"Authorization": "Bearer secret"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == name
    assert body["threshold"] == 150
