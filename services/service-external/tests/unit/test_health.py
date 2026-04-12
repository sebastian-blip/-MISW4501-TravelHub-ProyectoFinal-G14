"""HTTP smoke tests for root endpoints (Kafka off via tests/conftest.py)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from main import app


def test_health_returns_ok_and_integrations():
    with TestClient(app) as client:
        r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["service"] == "service-external"
    assert data["kafka_enabled"] is False
    assert "integrations" in data
    assert "pms" in data["integrations"]
    assert "payment" in data["integrations"]


def test_ready_returns_ready():
    with TestClient(app) as client:
        r = client.get("/ready")
    assert r.status_code == 200
    assert r.json().get("ready") is True
