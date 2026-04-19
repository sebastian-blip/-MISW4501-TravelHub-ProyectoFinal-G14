from __future__ import annotations

from pydantic import BaseModel


class GeocodeRequest(BaseModel):
    address_line: str
    city: str
    country_code: str


class GeocodeResult(BaseModel):
    latitude: float
    longitude: float
    formatted_address: str
    place_id: str


class PlaceSearchRequest(BaseModel):
    query: str


class PlaceSummary(BaseModel):
    place_id: str
    name: str
    latitude: float
    longitude: float


class DirectionsRequest(BaseModel):
    origin_place_id: str = ""
    destination_place_id: str = ""


class DirectionsSummary(BaseModel):
    distance_meters: int
    duration_seconds: int
    polyline: str | None = None
