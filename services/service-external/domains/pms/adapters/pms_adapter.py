from __future__ import annotations

from domains.pms.ports.pms_port import PMSIntegrationPort
from domains.pms.adapters.pms_client import PMSClient
from domains.pms.contracts import (
    AvailabilityQuery,
    AvailabilitySlot,
    PMSBookingPayload,
    PMSCatalogSnapshot,
    WebhookRegistration,
)
from resilience import CircuitBreaker, retry_with_backoff


class PMSAdapter(PMSIntegrationPort):
    """Driven adapter — calls the PMS provider via PMSClient."""

    def __init__(
        self,
        client: PMSClient | None = None,
        circuit_breaker: CircuitBreaker | None = None,
    ):
        self._client = client or PMSClient()
        self._breaker = circuit_breaker or CircuitBreaker()

    def _run(self, fn):
        if not self._breaker.allow():
            raise RuntimeError("pms_circuit_open")
        try:
            out = retry_with_backoff(fn)
            self._breaker.record_success()
            return out
        except Exception:
            self._breaker.record_failure()
            raise

    def fetch_catalog_snapshot(self, hotel_external_id: str) -> PMSCatalogSnapshot:
        return self._run(lambda: self._client.get_catalog(hotel_external_id))

    def query_availability(self, query: AvailabilityQuery) -> list[AvailabilitySlot]:
        return self._run(lambda: self._client.get_availability(query))

    def push_booking_confirmation(self, payload: PMSBookingPayload) -> None:
        self._run(lambda: self._client.post_booking(payload))

    def register_inventory_webhook(self, registration: WebhookRegistration) -> str:
        return self._run(lambda: self._client.register_webhook(registration).webhook_id)
