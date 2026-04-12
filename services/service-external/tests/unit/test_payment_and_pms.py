"""Tests for payment intents, PMS catalog (reservation-related HTTP), and mock adapters."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from domains.payment.adapters.mock_adapter import MockPaymentAdapter
from domains.payment.contracts import PaymentIntentRequest, RefundRequest
from domains.pms.adapters.mock_adapter import MockPMSAdapter
from main import app


class TestMockPaymentAdapter:
    def test_create_payment_intent_returns_mock_pi(self):
        adapter = MockPaymentAdapter()
        result = adapter.create_payment_intent(
            PaymentIntentRequest(
                amount_cents=52500,
                currency="USD",
                customer_payment_token="tok_test",
            )
        )
        assert result.id.startswith("pi_mock_")
        assert result.status == "requires_capture"
        assert result.client_secret and result.client_secret.startswith("cs_mock_")

    def test_refund_returns_succeeded(self):
        adapter = MockPaymentAdapter()
        out = adapter.refund(RefundRequest(payment_intent_id="pi_123", amount_cents=1000))
        assert out.status == "succeeded"
        assert out.refund_id.startswith("re_mock_")


class TestMockPMSAdapter:
    def test_fetch_catalog_snapshot_includes_hotel_and_room_types(self):
        adapter = MockPMSAdapter()
        snap = adapter.fetch_catalog_snapshot("ext-hotel-42")
        assert snap.hotel_external_id == "ext-hotel-42"
        assert "Mock Hotel" in snap.property_name
        assert len(snap.room_types) >= 2
        assert any(rt["id"] == "std" for rt in snap.room_types)


class TestPaymentHTTP:
    def test_create_payment_intent_ok(self):
        with TestClient(app) as client:
            r = client.post(
                "/payment/v1/payment-intents",
                json={
                    "amount_cents": 10000,
                    "currency": "USD",
                    "customer_payment_token": "tok_visa",
                },
            )
        assert r.status_code == 200
        data = r.json()
        assert data["id"].startswith("pi_mock_")
        assert data["status"] == "requires_capture"
        assert data.get("client_secret", "").startswith("cs_mock_")

    def test_create_payment_intent_validation_rejects_short_currency(self):
        with TestClient(app) as client:
            r = client.post(
                "/payment/v1/payment-intents",
                json={
                    "amount_cents": 100,
                    "currency": "US",
                    "customer_payment_token": "tok",
                },
            )
        assert r.status_code == 422


class TestPMSHTTP:
    def test_catalog_snapshot_ok(self):
        with TestClient(app) as client:
            r = client.get("/pms/v1/catalog/hotel-ext-001")
        assert r.status_code == 200
        data = r.json()
        assert data["hotel_external_id"] == "hotel-ext-001"
        assert data["property_name"]
        assert isinstance(data["room_types"], list)
        assert len(data["room_types"]) >= 1
