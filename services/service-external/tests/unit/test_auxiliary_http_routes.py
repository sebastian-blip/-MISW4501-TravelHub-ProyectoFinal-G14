"""HTTP routes for CDN, maps, notification (mock adapters via conftest)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from domains.notification.adapters.mock_adapter import MockNotificationAdapter
from domains.notification.contracts import PushNotificationRequest, SmsNotificationRequest
from main import app


def test_mock_notification_sms_and_push():
    adapter = MockNotificationAdapter()
    sms = adapter.enqueue_sms(SmsNotificationRequest(phone="+57300", template_id="t1"))
    assert sms.queue_message_id.startswith("mock-sms-")
    push = adapter.enqueue_push(PushNotificationRequest(user_id="u1", title="hi", body="there"))
    assert push.queue_message_id.startswith("mock-push-")


def test_cdn_signed_urls_ok():
    with TestClient(app) as client:
        r = client.post(
            "/cdn-storage/v1/signed-urls",
            json={"asset_id": "asset-42", "expires_seconds": 120},
        )
    assert r.status_code == 200
    data = r.json()
    assert "asset-42" in data["url"]


def test_maps_geocode_ok():
    with TestClient(app) as client:
        r = client.get(
            "/maps/v1/geocode",
            params={"address_line": "Kr 7", "city": "Bogotá", "country_code": "co"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["latitude"] == pytest.approx(4.6097)


def test_notification_enqueue_email_ok():
    with TestClient(app) as client:
        r = client.post(
            "/notification/v1/notifications/email",
            json={
                "to": "user@example.com",
                "template_id": "booking-confirm",
                "locale": "es",
                "variables": {"name": "Ana"},
            },
        )
    assert r.status_code == 200
    assert r.json()["status"] == "queued"
