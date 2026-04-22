"""Pytest hooks for service-external.

Kafka is disabled before any test imports `main`, so lifespan does not connect
to a broker during unit tests.
"""
from __future__ import annotations

import os

import pytest

os.environ["KAFKA_ENABLED"] = "false"
os.environ["KAFKA_BOOTSTRAP_SERVERS"] = ""

# HTTP integration routes use mock adapters (no real gateway/PMS calls in unit tests).
os.environ["PAYMENT_ADAPTER_STRATEGY"] = "mock"
os.environ["PMS_ADAPTER_STRATEGY"] = "mock"
os.environ["CURRENCY_ADAPTER_STRATEGY"] = "mock"
os.environ["CDN_STORAGE_ADAPTER_STRATEGY"] = "mock"
os.environ["MAPS_ADAPTER_STRATEGY"] = "mock"
os.environ["NOTIFICATION_ADAPTER_STRATEGY"] = "mock"

# Stable random-mode tests if the consumer module was imported with compose-style env.
os.environ.setdefault("TH_MOCK_RESERVATION_EXISTS_RATE", "0.25")


@pytest.fixture(autouse=True)
def _reset_pms_adapter_cache():
    """`routes/pms` and Kafka validate share `domains.pms.cached_adapter`."""
    from domains.pms.cached_adapter import reset_cached_pms_adapter

    reset_cached_pms_adapter()
    yield
    reset_cached_pms_adapter()
