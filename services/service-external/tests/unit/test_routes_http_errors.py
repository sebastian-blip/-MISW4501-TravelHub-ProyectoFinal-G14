"""HTTP 502/503 branches on integration routes."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import routes.cdn_storage as cdn_routes
import routes.currency as currency_routes
import routes.maps as maps_routes
import routes.notification as notification_routes
import routes.payment as payment_routes
import routes.pms as pms_routes
from main import app


@pytest.fixture(autouse=True)
def _reset_route_adapters():
    """Avoid leaking patched adapters between tests."""
    for mod in (cdn_routes, currency_routes, maps_routes, notification_routes, payment_routes):
        mod._adapter = None
    yield
    for mod in (cdn_routes, currency_routes, maps_routes, notification_routes, payment_routes):
        mod._adapter = None


def test_currency_rates_503_on_circuit():
    class A:
        def get_rate(self, q):
            raise RuntimeError("fx_circuit_open")

    with patch.object(currency_routes, "get_adapter", return_value=A()):
        with TestClient(app) as client:
            r = client.get("/currency/v1/rates", params={"base": "USD", "quote": "COP"})
    assert r.status_code == 503


def test_currency_rates_502_on_other_runtime():
    class A:
        def get_rate(self, q):
            raise RuntimeError("fx_upstream_http_500")

    with patch.object(currency_routes, "get_adapter", return_value=A()):
        with TestClient(app) as client:
            r = client.get("/currency/v1/rates", params={"base": "USD", "quote": "COP"})
    assert r.status_code == 502


def test_currency_convert_503_on_circuit():
    class A:
        def convert(self, body):
            raise RuntimeError("fx_circuit_open")

    with patch.object(currency_routes, "get_adapter", return_value=A()):
        with TestClient(app) as client:
            r = client.post(
                "/currency/v1/convert",
                json={"amount": "1", "from_currency": "USD", "to_currency": "COP"},
            )
    assert r.status_code == 503


def test_payment_intent_503_on_circuit():
    class A:
        def create_payment_intent(self, req):
            raise RuntimeError("payment_gateway_circuit_open")

    with patch.object(payment_routes, "get_adapter", return_value=A()):
        with TestClient(app) as client:
            r = client.post(
                "/payment/v1/payment-intents",
                json={"amount_cents": 1, "currency": "USD", "customer_payment_token": "t"},
            )
    assert r.status_code == 503


def test_cdn_503_on_circuit():
    class A:
        def create_signed_read_url(self, req):
            raise RuntimeError("storage_circuit_open")

    with patch.object(cdn_routes, "get_adapter", return_value=A()):
        with TestClient(app) as client:
            r = client.post("/cdn-storage/v1/signed-urls", json={"asset_id": "x", "expires_seconds": 120})
    assert r.status_code == 503


def test_maps_503_on_circuit():
    class A:
        def geocode(self, req):
            raise RuntimeError("maps_circuit_open")

    with patch.object(maps_routes, "get_adapter", return_value=A()):
        with TestClient(app) as client:
            r = client.get("/maps/v1/geocode", params={"address_line": "a", "city": "b", "country_code": "CO"})
    assert r.status_code == 503


def test_notification_503_on_circuit():
    class A:
        def enqueue_email(self, req):
            raise RuntimeError("notification_provider_circuit_open")

    with patch.object(notification_routes, "get_adapter", return_value=A()):
        with TestClient(app) as client:
            r = client.post(
                "/notification/v1/notifications/email",
                json={"to": "u@example.com", "template_id": "t1"},
            )
    assert r.status_code == 503


def test_currency_rates_502_on_generic_exception():
    class A:
        def get_rate(self, q):
            raise ValueError("unexpected")

    with patch.object(currency_routes, "get_adapter", return_value=A()):
        with TestClient(app) as client:
            r = client.get("/currency/v1/rates", params={"base": "USD", "quote": "COP"})
    assert r.status_code == 502


def test_payment_intent_502_on_generic_exception():
    class A:
        def create_payment_intent(self, req):
            raise ValueError("bad payload")

    with patch.object(payment_routes, "get_adapter", return_value=A()):
        with TestClient(app) as client:
            r = client.post(
                "/payment/v1/payment-intents",
                json={"amount_cents": 1, "currency": "USD", "customer_payment_token": "t"},
            )
    assert r.status_code == 502


def test_pms_catalog_503_on_circuit_runtime_error():
    class BadPms:
        def fetch_catalog_snapshot(self, hotel_external_id: str):
            raise RuntimeError("pms_circuit_open")

    with patch.object(pms_routes, "get_adapter", new=lambda: BadPms()):
        with TestClient(app) as client:
            r = client.get("/pms/v1/catalog/hotel-x")
    assert r.status_code == 503


def test_pms_catalog_runtime_error_without_circuit_returns_500_response():
    class BadPms:
        def fetch_catalog_snapshot(self, hotel_external_id: str):
            raise RuntimeError("transient without circuit keyword")

    with patch.object(pms_routes, "get_adapter", new=lambda: BadPms()):
        with TestClient(app, raise_server_exceptions=False) as client:
            r = client.get("/pms/v1/catalog/hotel-x")
    assert r.status_code == 500


def test_pms_catalog_502_on_generic_exception():
    class BadPms:
        def fetch_catalog_snapshot(self, hotel_external_id: str):
            raise ValueError("pms exploded")

    with patch.object(pms_routes, "get_adapter", new=lambda: BadPms()):
        with TestClient(app) as client:
            r = client.get("/pms/v1/catalog/hotel-x")
    assert r.status_code == 502


def test_cdn_502_on_generic_exception():
    class A:
        def create_signed_read_url(self, req):
            raise TypeError("bad")

    with patch.object(cdn_routes, "get_adapter", return_value=A()):
        with TestClient(app) as client:
            r = client.post("/cdn-storage/v1/signed-urls", json={"asset_id": "x", "expires_seconds": 120})
    assert r.status_code == 502


def test_maps_502_on_generic_exception():
    class A:
        def geocode(self, req):
            raise TypeError("bad")

    with patch.object(maps_routes, "get_adapter", return_value=A()):
        with TestClient(app) as client:
            r = client.get("/maps/v1/geocode", params={"address_line": "a", "city": "b", "country_code": "CO"})
    assert r.status_code == 502


def test_notification_502_on_generic_exception():
    class A:
        def enqueue_email(self, req):
            raise TypeError("bad")

    with patch.object(notification_routes, "get_adapter", return_value=A()):
        with TestClient(app) as client:
            r = client.post(
                "/notification/v1/notifications/email",
                json={"to": "u@example.com", "template_id": "t1"},
            )
    assert r.status_code == 502


def test_currency_convert_502_on_generic_exception():
    class A:
        def convert(self, body):
            raise TypeError("bad")

    with patch.object(currency_routes, "get_adapter", return_value=A()):
        with TestClient(app) as client:
            r = client.post(
                "/currency/v1/convert",
                json={"amount": "1", "from_currency": "USD", "to_currency": "COP"},
            )
    assert r.status_code == 502
