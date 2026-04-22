from __future__ import annotations

from domains.maps.ports.location_port import LocationPort
from domains.maps.adapters.maps_client import MapsClient
from domains.maps.contracts import (
    DirectionsRequest,
    DirectionsSummary,
    GeocodeRequest,
    GeocodeResult,
    PlaceSearchRequest,
    PlaceSummary,
)
from resilience import CircuitBreaker, retry_with_backoff


class MapsLocationAdapter(LocationPort):
    """Driven adapter — calls the maps provider via MapsClient."""

    def __init__(
        self,
        client: MapsClient | None = None,
        circuit_breaker: CircuitBreaker | None = None,
    ):
        self._client = client or MapsClient()
        self._breaker = circuit_breaker or CircuitBreaker(failure_threshold=10)

    def _run(self, fn):
        if not self._breaker.allow():
            raise RuntimeError("maps_circuit_open")
        try:
            out = retry_with_backoff(fn, max_attempts=3)
            self._breaker.record_success()
            return out
        except Exception:
            self._breaker.record_failure()
            raise

    def geocode(self, request: GeocodeRequest) -> GeocodeResult:
        return self._run(lambda: self._client.geocode(request))

    def search_places(self, request: PlaceSearchRequest) -> list[PlaceSummary]:
        return self._run(lambda: self._client.places_search(request))

    def directions(self, request: DirectionsRequest) -> DirectionsSummary:
        return self._run(lambda: self._client.directions(request))
