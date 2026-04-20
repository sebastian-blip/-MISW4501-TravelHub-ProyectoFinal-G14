"""`main` lifespan + `/ready` flags."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

import main as main_mod


def test_ready_skipped_when_env_set(monkeypatch):
    monkeypatch.setenv("TH_PAYMENT_SKIP_READY", "true")
    with TestClient(main_mod.app) as client:
        r = client.get("/ready")
    assert r.status_code == 200
    assert r.json() == {"ready": True, "skipped": True}


def test_lifespan_kafka_start_failure_is_swallowed(monkeypatch):
    monkeypatch.setattr(main_mod, "KAFKA_ENABLED", True)
    monkeypatch.setattr(main_mod, "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    async def boom(_bs: str):
        raise RuntimeError("broker unavailable")

    with patch.object(main_mod, "start_kafka_consumers", boom):
        with patch.object(main_mod, "stop_kafka_consumers", new_callable=AsyncMock):
            with TestClient(main_mod.app) as client:
                r = client.get("/health")
    assert r.status_code == 200


def test_lifespan_kafka_stop_failure_is_swallowed(monkeypatch):
    monkeypatch.setattr(main_mod, "KAFKA_ENABLED", True)
    monkeypatch.setattr(main_mod, "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    async def ok_start(_bs: str):
        return None

    async def bad_stop():
        raise RuntimeError("stop failed")

    with patch.object(main_mod, "start_kafka_consumers", ok_start):
        with patch.object(main_mod, "stop_kafka_consumers", bad_stop):
            with TestClient(main_mod.app) as client:
                assert client.get("/health").status_code == 200
