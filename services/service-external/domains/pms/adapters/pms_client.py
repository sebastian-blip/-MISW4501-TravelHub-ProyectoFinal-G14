from __future__ import annotations

import uuid
from types import SimpleNamespace

from domains.pms.contracts import (
    AvailabilityQuery,
    AvailabilitySlot,
    PMSBookingPayload,
    PMSCatalogSnapshot,
    WebhookRegistration,
)


class PMSClient:
    def get_catalog(self, hotel_external_id: str) -> PMSCatalogSnapshot:
        return PMSCatalogSnapshot(
            hotel_external_id=hotel_external_id,
            property_name=f"Stub Hotel {hotel_external_id}",
            room_types=[{"id": "std", "name": "Standard"}],
        )

    def get_availability(self, query: AvailabilityQuery) -> list[AvailabilitySlot]:
        from datetime import timedelta
        from decimal import Decimal

        days = max((query.check_out - query.check_in).days, 1)
        return [
            AvailabilitySlot(
                date=query.check_in + timedelta(days=i),
                available_units=3,
                rate=Decimal("120.00"),
                currency="USD",
            )
            for i in range(days)
        ]

    def post_booking(self, payload: PMSBookingPayload) -> None:
        _ = payload

    def register_webhook(self, registration: WebhookRegistration) -> SimpleNamespace:
        _ = registration
        return SimpleNamespace(webhook_id=f"wh_{uuid.uuid4().hex[:10]}")
