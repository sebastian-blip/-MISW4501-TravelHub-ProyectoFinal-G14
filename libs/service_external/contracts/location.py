from __future__ import annotations

from pydantic import BaseModel, Field


class GeocodeRequest(BaseModel):
    address_line: str
    city: str
    country_code: str = Field(min_length=2, max_length=2)


class GeocodeResult(BaseModel):
    latitude: float
    longitude: float
    formatted_address: str
    place_id: str | None = None


class PlaceSearchRequest(BaseModel):
    query: str
    latitude: float | None = None
    longitude: float | None = None
    radius_meters: int | None = None


class PlaceSummary(BaseModel):
    place_id: str
    name: str
    latitude: float
    longitude: float


class DirectionsRequest(BaseModel):
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float


class DirectionsSummary(BaseModel):
    distance_meters: int
    duration_seconds: int
    polyline: str | None = None
