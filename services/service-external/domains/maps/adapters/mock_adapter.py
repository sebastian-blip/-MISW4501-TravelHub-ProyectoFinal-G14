from __future__ import annotations

from domains.maps.ports.location_port import LocationPort
from domains.maps.contracts import (
    DirectionsRequest,
    DirectionsSummary,
    GeocodeRequest,
    GeocodeResult,
    PlaceSearchRequest,
    PlaceSummary,
)


class MockLocationAdapter(LocationPort):
    """In-memory stub for local development and testing."""

    def geocode(self, request: GeocodeRequest) -> GeocodeResult:
        return GeocodeResult(
            latitude=4.6097,
            longitude=-74.0817,
            formatted_address=f"{request.address_line}, {request.city}",
            place_id="mock-place-1",
        )

    def search_places(self, request: PlaceSearchRequest) -> list[PlaceSummary]:
        return [PlaceSummary(place_id="mock-place-1", name=f"Mock: {request.query}", latitude=4.6097, longitude=-74.0817)]

    def directions(self, request: DirectionsRequest) -> DirectionsSummary:
        return DirectionsSummary(distance_meters=5000, duration_seconds=600, polyline=None)
