from dataclasses import dataclass
from typing import Optional, List
from uuid import UUID


@dataclass
class HotelResponse:
    id: UUID
    name: str
    city: str
    country: str
    address: str
    stars: int
    active: bool

    @classmethod
    def from_orm(cls, hotel) -> "HotelResponse":
        return cls(
            id=hotel.id,
            name=hotel.name,
            city=hotel.city,
            country=hotel.country,
            address=hotel.address,
            stars=hotel.stars,
            active=hotel.active,
        )


@dataclass
class GetHotelsQuery:
    city: Optional[str] = None