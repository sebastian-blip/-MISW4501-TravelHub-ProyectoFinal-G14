"""Exercise real (stub-client) driven adapters for coverage."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest

from domains.cdn_storage.adapters.cdn_storage_adapter import CDNStorageAdapter
from domains.cdn_storage.contracts import SignedUrlRequest, UploadRequest
from domains.maps.adapters.maps_location_adapter import MapsLocationAdapter
from domains.maps.contracts import DirectionsRequest, GeocodeRequest, PlaceSearchRequest
from domains.notification.adapters.email_sms_adapter import EmailSmsAdapter
from domains.notification.contracts import (
    EmailNotificationRequest,
    PushNotificationRequest,
    SmsNotificationRequest,
)
from domains.payment.adapters.payment_gateway_adapter import PaymentGatewayAdapter
from domains.payment.contracts import PaymentIntentRequest, RefundRequest
from domains.pms.adapters.pms_adapter import PMSAdapter
from domains.pms.contracts import (
    AvailabilityQuery,
    PMSBookingPayload,
    WebhookRegistration,
)
from resilience import CircuitBreaker


def test_cdn_storage_adapter_round_trip():
    adapter = CDNStorageAdapter()
    up = adapter.upload(UploadRequest(body_bytes=b"hello", content_type="text/plain"))
    assert up.asset_id.startswith("stub-")
    signed = adapter.create_signed_read_url(SignedUrlRequest(asset_id=up.asset_id, expires_seconds=120))
    assert up.asset_id in signed.url
    adapter.delete_asset(up.asset_id)


def test_cdn_storage_adapter_circuit_open():
    client = MagicMock()
    client.signed_url.side_effect = RuntimeError("boom")
    breaker = CircuitBreaker(failure_threshold=1)
    adapter = CDNStorageAdapter(client=client, circuit_breaker=breaker)
    with pytest.raises(RuntimeError, match="boom"):
        adapter.create_signed_read_url(SignedUrlRequest(asset_id="a1", expires_seconds=120))
    with pytest.raises(RuntimeError, match="storage_circuit_open"):
        adapter.create_signed_read_url(SignedUrlRequest(asset_id="a1", expires_seconds=120))


def test_maps_location_adapter_all_methods():
    adapter = MapsLocationAdapter()
    g = adapter.geocode(GeocodeRequest(address_line="Cll 1", city="Bogotá", country_code="CO"))
    assert g.latitude == pytest.approx(4.6097)
    places = adapter.search_places(PlaceSearchRequest(query="cafe"))
    assert len(places) == 1
    d = adapter.directions(DirectionsRequest(origin_place_id="a", destination_place_id="b"))
    assert d.distance_meters == 1000


def test_maps_location_adapter_circuit_open():
    client = MagicMock()
    client.geocode.side_effect = RuntimeError("down")
    breaker = CircuitBreaker(failure_threshold=1)
    adapter = MapsLocationAdapter(client=client, circuit_breaker=breaker)
    with pytest.raises(RuntimeError, match="down"):
        adapter.geocode(GeocodeRequest(address_line="x", city="y", country_code="CO"))
    with pytest.raises(RuntimeError, match="maps_circuit_open"):
        adapter.geocode(GeocodeRequest(address_line="x", city="y", country_code="CO"))


def test_email_sms_adapter_all_channels():
    adapter = EmailSmsAdapter()
    e = adapter.enqueue_email(
        EmailNotificationRequest(to="a@example.com", template_id="t1", locale="es", variables={})
    )
    assert e.status == "queued"
    s = adapter.enqueue_sms(SmsNotificationRequest(phone="+573001234567", template_id="sms1"))
    assert s.queue_message_id.startswith("sms-")
    p = adapter.enqueue_push(PushNotificationRequest(user_id="u1", title="t", body="b"))
    assert p.queue_message_id.startswith("push-")


def test_email_sms_adapter_circuit_open():
    client = MagicMock()
    client.post_email.side_effect = RuntimeError("smtp down")
    breaker = CircuitBreaker(failure_threshold=1)
    adapter = EmailSmsAdapter(client=client, circuit_breaker=breaker)
    with pytest.raises(RuntimeError, match="smtp down"):
        adapter.enqueue_email(
            EmailNotificationRequest(to="a@example.com", template_id="t", locale="es", variables={})
        )
    with pytest.raises(RuntimeError, match="notification_provider_circuit_open"):
        adapter.enqueue_email(
            EmailNotificationRequest(to="a@example.com", template_id="t", locale="es", variables={})
        )


def test_payment_gateway_adapter_full_flow():
    adapter = PaymentGatewayAdapter()
    pi = adapter.create_payment_intent(
        PaymentIntentRequest(amount_cents=500, currency="USD", customer_payment_token="tok_x")
    )
    assert pi.id.startswith("pi_mock_")
    cap = adapter.capture_payment(pi.id, amount_cents=500)
    assert cap.status == "succeeded"
    cap_none = adapter.capture_payment(pi.id, amount_cents=None)
    assert cap_none.status == "succeeded"
    ref = adapter.refund(RefundRequest(payment_intent_id=pi.id, amount_cents=100, reason="test"))
    assert ref.refund_id.startswith("re_")
    ref_min = adapter.refund(RefundRequest(payment_intent_id=pi.id))
    assert ref_min.status == "succeeded"
    tok = adapter.tokenize_payment_method("tr_tok")
    assert tok.last4 == "4242"


def test_payment_gateway_adapter_circuit_open():
    client = MagicMock()
    client.build_intent_body.return_value = {}
    client.create_intent.side_effect = RuntimeError("gw")
    breaker = CircuitBreaker(failure_threshold=1)
    adapter = PaymentGatewayAdapter(client=client, circuit_breaker=breaker)
    req = PaymentIntentRequest(amount_cents=1, currency="USD", customer_payment_token="t")
    with pytest.raises(RuntimeError, match="gw"):
        adapter.create_payment_intent(req)
    with pytest.raises(RuntimeError, match="payment_gateway_circuit_open"):
        adapter.create_payment_intent(req)


def test_pms_adapter_all_methods():
    adapter = PMSAdapter()
    cat = adapter.fetch_catalog_snapshot("hotel-1")
    assert cat.hotel_external_id == "hotel-1"
    q = AvailabilityQuery(
        hotel_external_id="hotel-1",
        check_in=date(2030, 1, 1),
        check_out=date(2030, 1, 3),
        room_type_external_id=None,
    )
    slots = adapter.query_availability(q)
    assert len(slots) == 2
    assert all(s.available_units == 3 for s in slots)
    adapter.push_booking_confirmation(
        PMSBookingPayload(external_booking_id="b1", hotel_external_id="hotel-1", guest_email="g@e.co")
    )
    wid = adapter.register_inventory_webhook(
        WebhookRegistration(hotel_external_id="hotel-1", callback_url="https://ex.co/h")
    )
    assert wid.startswith("wh_")


def test_pms_adapter_circuit_open():
    client = MagicMock()
    client.get_catalog.side_effect = RuntimeError("pms err")
    breaker = CircuitBreaker(failure_threshold=1)
    adapter = PMSAdapter(client=client, circuit_breaker=breaker)
    with pytest.raises(RuntimeError, match="pms err"):
        adapter.fetch_catalog_snapshot("x")
    with pytest.raises(RuntimeError, match="pms_circuit_open"):
        adapter.fetch_catalog_snapshot("x")
