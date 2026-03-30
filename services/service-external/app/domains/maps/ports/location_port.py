from __future__ import annotations

from abc import ABC, abstractmethod

from service_external.contracts.location import (
    DirectionsRequest,
    DirectionsSummary,
    GeocodeRequest,
    GeocodeResult,
    PlaceSearchRequest,
    PlaceSummary,
)


class LocationPort(ABC):
    """Contract that any maps/location adapter must implement."""

    @abstractmethod
    def geocode(self, request: GeocodeRequest) -> GeocodeResult: ...

    @abstractmethod
    def search_places(self, request: PlaceSearchRequest) -> list[PlaceSummary]: ...

    @abstractmethod
    def directions(self, request: DirectionsRequest) -> DirectionsSummary: ...
