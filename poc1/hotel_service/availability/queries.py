from dataclasses import dataclass
from typing import List, Optional
import logging
import time
from uuid import UUID

from mediatr import Mediator

from hotel_service.availability.repository import HotelAvailabilityRepository
from domain.models.hotel_availability import HotelAvailability


@dataclass
class SearchAvailableHotelsQuery:
    city: Optional[str] = None


@dataclass
class AvailableHotelResponse:
    hotel_id: UUID
    room_id: UUID
    hotel_name: str
    city: str
    available: bool
    room_type: Optional[str]
    price_per_night: Optional[float]

    @classmethod
    def from_model(cls, availability: HotelAvailability) -> "AvailableHotelResponse":
        price = availability.price_per_night
        return cls(
            hotel_id=UUID(str(availability.hotel_id)),
            room_id=UUID(str(availability.room_id)),
            hotel_name=availability.hotel_name,
            city=availability.city,
            available=availability.available,
            room_type=availability.room_type,
            price_per_night=float(price) if price is not None else None,
        )


@Mediator.handler
class SearchAvailableHotelsQueryHandler:

    def __init__(self):
        self.repository = HotelAvailabilityRepository()

    async def handle(self, query: SearchAvailableHotelsQuery) -> List[AvailableHotelResponse]:
        availabilities = await self.repository.get_available(query.city)
        logging.info({
            "event": "available_rooms_retrieved",
            "city": query.city or "any",
            "available_count": len(availabilities),
            "timestamp": time.time(),
        })
        return [AvailableHotelResponse.from_model(a) for a in availabilities]
