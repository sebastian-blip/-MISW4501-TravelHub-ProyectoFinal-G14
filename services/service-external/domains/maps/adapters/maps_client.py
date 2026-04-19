from __future__ import annotations

from domains.maps.contracts import (
    DirectionsRequest,
    DirectionsSummary,
    GeocodeRequest,
    GeocodeResult,
    PlaceSearchRequest,
    PlaceSummary,
)


class MapsClient:
    def geocode(self, request: GeocodeRequest) -> GeocodeResult:
        return GeocodeResult(
            latitude=4.6097,
            longitude=-74.0817,
            formatted_address=f"{request.address_line}, {request.city}",
            place_id="stub-place",
        )

    def places_search(self, request: PlaceSearchRequest) -> list[PlaceSummary]:
        return [
            PlaceSummary(
                place_id="stub-1",
                name=f"Stub: {request.query}",
                latitude=4.6097,
                longitude=-74.0817,
            )
        ]

    def directions(self, request: DirectionsRequest) -> DirectionsSummary:
        _ = request
        return DirectionsSummary(distance_meters=1000, duration_seconds=120, polyline=None)
