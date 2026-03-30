from __future__ import annotations

import httpx

from service_external.adapters.maps_location.config import MapsSettings
from service_external.contracts.location import (
    DirectionsRequest,
    DirectionsSummary,
    GeocodeRequest,
    GeocodeResult,
    PlaceSearchRequest,
    PlaceSummary,
)


class MapsClient:
    def __init__(self, settings: MapsSettings | None = None):
        self._s = settings or MapsSettings()
        self._client = httpx.Client(
            base_url=self._s.base_url.rstrip("/"),
            timeout=self._s.timeout_seconds,
            verify=self._s.verify_tls,
            params={"key": self._s.api_key} if self._s.api_key else {},
        )

    def close(self) -> None:
        self._client.close()

    def geocode(self, request: GeocodeRequest) -> GeocodeResult:
        r = self._client.get(
            "/geocode",
            params={
                "address": request.address_line,
                "city": request.city,
                "country": request.country_code,
            },
        )
        r.raise_for_status()
        data = r.json()
        return GeocodeResult(
            latitude=data["latitude"],
            longitude=data["longitude"],
            formatted_address=data["formatted_address"],
            place_id=data.get("place_id"),
        )

    def places_search(self, request: PlaceSearchRequest) -> list[PlaceSummary]:
        params: dict = {"q": request.query}
        if request.latitude is not None:
            params["lat"] = request.latitude
        if request.longitude is not None:
            params["lng"] = request.longitude
        if request.radius_meters is not None:
            params["radius_m"] = request.radius_meters
        r = self._client.get("/places/search", params=params)
        r.raise_for_status()
        return [PlaceSummary.model_validate(x) for x in r.json().get("results", [])]

    def directions(self, request: DirectionsRequest) -> DirectionsSummary:
        r = self._client.get(
            "/directions",
            params={
                "olat": request.origin_lat,
                "olng": request.origin_lng,
                "dlat": request.dest_lat,
                "dlng": request.dest_lng,
            },
        )
        r.raise_for_status()
        data = r.json()
        return DirectionsSummary(
            distance_meters=int(data["distance_meters"]),
            duration_seconds=int(data["duration_seconds"]),
            polyline=data.get("polyline"),
        )
