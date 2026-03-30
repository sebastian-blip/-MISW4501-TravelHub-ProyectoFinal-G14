from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from app.ports.pms_port import PMSIntegrationPort
from service_external.contracts.pms import (
    AvailabilityQuery,
    AvailabilitySlot,
    PMSBookingPayload,
    PMSCatalogSnapshot,
    WebhookRegistration,
)


class MockPMSAdapter(PMSIntegrationPort):
    """In-memory stub for local development and testing."""

    def fetch_catalog_snapshot(self, hotel_external_id: str) -> PMSCatalogSnapshot:
        return PMSCatalogSnapshot(
            hotel_external_id=hotel_external_id,
            property_name=f"Mock Hotel {hotel_external_id}",
            room_types=[{"id": "std", "name": "Standard"}, {"id": "dlx", "name": "Deluxe"}],
        )

    def query_availability(self, query: AvailabilityQuery) -> list[AvailabilitySlot]:
        days = (query.check_out - query.check_in).days
        return [
            AvailabilitySlot(date=query.check_in + timedelta(days=i), available_units=5, rate=Decimal("100.00"), currency="USD")
            for i in range(max(days, 1))
        ]

    def push_booking_confirmation(self, payload: PMSBookingPayload) -> None:
        pass

    def register_inventory_webhook(self, registration: WebhookRegistration) -> str:
        return "mock-webhook-id"
