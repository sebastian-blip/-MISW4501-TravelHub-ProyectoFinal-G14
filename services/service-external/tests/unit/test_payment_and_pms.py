"""Tests for payment, PMS HTTP routes, mock adapters, and shared PMS cache."""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient

from domains.pms.adapters.mock_adapter import MockPMSAdapter
from domains.pms.cached_adapter import get_cached_pms_adapter, reset_cached_pms_adapter
from domains.pms.contracts import AvailabilityQuery, WebhookRegistration
from domains.payment.adapters.mock_adapter import MockPaymentAdapter
from domains.payment.contracts import PaymentIntentRequest, RefundRequest
from main import app


class TestCachedPMSAdapter:
    def test_get_cached_pms_adapter_returns_singleton(self):
        reset_cached_pms_adapter()
        a = get_cached_pms_adapter()
        b = get_cached_pms_adapter()
        assert a is b

    def test_reset_cached_pms_adapter_creates_new_instance_on_next_get(self):
        reset_cached_pms_adapter()
        first = get_cached_pms_adapter()
        reset_cached_pms_adapter()
        second = get_cached_pms_adapter()
        assert second is not first


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

    def test_query_availability_returns_one_slot_per_night(self):
        adapter = MockPMSAdapter()
        q = AvailabilityQuery(
            hotel_external_id="h1",
            check_in=date(2030, 6, 1),
            check_out=date(2030, 6, 5),
            room_type_external_id="std",
        )
        slots = adapter.query_availability(q)
        assert len(slots) == 4
        assert all(s.available_units == 5 for s in slots)
        assert slots[0].date == date(2030, 6, 1)

    def test_register_webhook_returns_stable_mock_id(self):
        adapter = MockPMSAdapter()
        wid = adapter.register_inventory_webhook(
            WebhookRegistration(hotel_external_id="h1", callback_url="https://example.com/hook")
        )
        assert wid == "mock-webhook-id"

    def test_push_booking_confirmation_noop(self):
        from domains.pms.contracts import PMSBookingPayload

        adapter = MockPMSAdapter()
        adapter.push_booking_confirmation(
            PMSBookingPayload(external_booking_id="x", hotel_external_id="h", guest_email="a@b.co")
        )


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

    def test_availability_post_ok(self):
        with TestClient(app) as client:
            r = client.post(
                "/pms/v1/availability",
                json={
                    "hotel_external_id": "hotel-ext-001",
                    "check_in": "2030-06-01",
                    "check_out": "2030-06-05",
                },
            )
        assert r.status_code == 200
        rows = r.json()
        assert isinstance(rows, list)
        assert len(rows) == 4
        assert rows[0]["available_units"] == 5
        assert rows[0]["currency"] == "USD"

    def test_availability_post_accepts_room_type_external_id(self):
        with TestClient(app) as client:
            r = client.post(
                "/pms/v1/availability",
                json={
                    "hotel_external_id": "hotel-ext-001",
                    "check_in": "2030-07-01",
                    "check_out": "2030-07-02",
                    "room_type_external_id": "c1000000-0000-0000-0000-000000000101",
                },
            )
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_availability_post_validation_requires_dates(self):
        with TestClient(app) as client:
            r = client.post(
                "/pms/v1/availability",
                json={"hotel_external_id": "h1"},
            )
        assert r.status_code == 422

    def test_booking_confirmation_accepted(self):
        with TestClient(app) as client:
            r = client.post(
                "/pms/v1/bookings/confirmation",
                json={
                    "external_booking_id": "bk_123",
                    "hotel_external_id": "hotel-ext-001",
                    "guest_email": "guest@example.com",
                },
            )
        assert r.status_code == 200
        assert r.json() == {"status": "accepted"}

    def test_inventory_webhook_returns_id(self):
        with TestClient(app) as client:
            r = client.post(
                "/pms/v1/webhooks/inventory",
                json={
                    "hotel_external_id": "hotel-ext-001",
                    "callback_url": "https://example.com/inventory",
                },
            )
        assert r.status_code == 200
        assert r.json() == {"webhook_id": "mock-webhook-id"}
