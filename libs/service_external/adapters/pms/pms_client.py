from __future__ import annotations

import httpx

from service_external.adapters.pms.config import PMSSettings
from service_external.adapters.pms.schemas import WebhookRegisterResponse
from service_external.contracts.pms import (
    AvailabilityQuery,
    AvailabilitySlot,
    PMSBookingPayload,
    PMSCatalogSnapshot,
    WebhookRegistration,
)


class PMSClient:
    def __init__(self, settings: PMSSettings | None = None):
        self._s = settings or PMSSettings()
        headers: dict[str, str] = {}
        if self._s.api_key:
            headers["X-API-Key"] = self._s.api_key
        if self._s.oauth_token:
            headers["Authorization"] = f"Bearer {self._s.oauth_token}"
        self._client = httpx.Client(
            base_url=self._s.base_url.rstrip("/"),
            timeout=self._s.timeout_seconds,
            verify=self._s.verify_tls,
            headers=headers,
        )

    def close(self) -> None:
        self._client.close()

    def get_catalog(self, hotel_external_id: str) -> PMSCatalogSnapshot:
        r = self._client.get(f"/hotels/{hotel_external_id}/catalog")
        r.raise_for_status()
        data = r.json()
        return PMSCatalogSnapshot(
            hotel_external_id=data.get("hotel_external_id", hotel_external_id),
            property_name=data.get("property_name", ""),
            room_types=data.get("room_types", []),
        )

    def get_availability(self, query: AvailabilityQuery) -> list[AvailabilitySlot]:
        r = self._client.get(
            f"/hotels/{query.hotel_external_id}/availability",
            params={
                "check_in": query.check_in.isoformat(),
                "check_out": query.check_out.isoformat(),
                "room_type": query.room_type_external_id or "",
            },
        )
        r.raise_for_status()
        rows = r.json().get("slots", [])
        return [AvailabilitySlot.model_validate(x) for x in rows]

    def post_booking(self, payload: PMSBookingPayload) -> None:
        r = self._client.post(
            "/bookings/confirm",
            json={
                "reservation_id": str(payload.reservation_id),
                "hotel_external_id": payload.hotel_external_id,
                "guest_name": payload.guest_name,
                "check_in": payload.check_in.isoformat(),
                "check_out": payload.check_out.isoformat(),
                "external_confirmation_code": payload.external_confirmation_code,
            },
        )
        r.raise_for_status()

    def register_webhook(self, registration: WebhookRegistration) -> WebhookRegisterResponse:
        r = self._client.post(
            "/webhooks/inventory",
            json={
                "callback_url": registration.callback_url,
                "secret": registration.secret,
                "events": registration.events,
            },
        )
        r.raise_for_status()
        return WebhookRegisterResponse.model_validate(r.json())
