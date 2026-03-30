from __future__ import annotations

from abc import ABC, abstractmethod

from service_external.contracts.pms import (
    AvailabilityQuery,
    AvailabilitySlot,
    PMSBookingPayload,
    PMSCatalogSnapshot,
    WebhookRegistration,
)


class PMSIntegrationPort(ABC):
    """Contract that any PMS integration adapter must implement."""

    @abstractmethod
    def fetch_catalog_snapshot(self, hotel_external_id: str) -> PMSCatalogSnapshot: ...

    @abstractmethod
    def query_availability(self, query: AvailabilityQuery) -> list[AvailabilitySlot]: ...

    @abstractmethod
    def push_booking_confirmation(self, payload: PMSBookingPayload) -> None: ...

    @abstractmethod
    def register_inventory_webhook(self, registration: WebhookRegistration) -> str: ...
