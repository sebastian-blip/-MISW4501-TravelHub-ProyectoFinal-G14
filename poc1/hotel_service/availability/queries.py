from dataclasses import dataclass
from typing import List, Optional
import logging
import time
from uuid import UUID

from mediatr import Mediator
from dataclasses import dataclass
from typing import List, Optional, Tuple
import logging
import time
from uuid import UUID

from mediatr import Mediator

from hotel_service.availability.repository import HotelAvailabilityRepository
from domain.models.hotel_availability import HotelAvailability


@dataclass
class SearchAvailableHotelsQuery:
    city: Optional[str] = None
    skip: int = 0
    limit: int = 10


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
    def from_model(cls,
                   availability: HotelAvailability) -> "AvailableHotelResponse":
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


@dataclass
class PaginatedAvailableHotelsResponse:
    """Respuesta con paginación"""
    data: List[AvailableHotelResponse]
    total: int
    skip: int
    limit: int
    page: int
    total_pages: int

    @classmethod
    def from_availabilities(
            cls,
            availabilities: List[HotelAvailability],
            total: int,
            skip: int,
            limit: int,
    ) -> "PaginatedAvailableHotelsResponse":
        page = (skip // limit) + 1
        total_pages = (total + limit - 1) // limit

        return cls(
            data=[AvailableHotelResponse.from_model(a) for a in availabilities],
            total=total,
            skip=skip,
            limit=limit,
            page=page,
            total_pages=total_pages,
        )


@Mediator.handler
class SearchAvailableHotelsQueryHandler:

    def __init__(self):
        self.repository = HotelAvailabilityRepository()

    async def handle(self,
                     query: SearchAvailableHotelsQuery) -> PaginatedAvailableHotelsResponse:
        start_time = time.time()

        availabilities, total = await self.repository.get_available(
            city=query.city,
            skip=query.skip,
            limit=query.limit
        )

        response = PaginatedAvailableHotelsResponse.from_availabilities(
            availabilities=availabilities,
            total=total,
            skip=query.skip,
            limit=query.limit,
        )

        elapsed = time.time() - start_time

        logging.info({
            "event": "available_rooms_retrieved",
            "city": query.city or "any",
            "total_count": response.total,
            "paginated_count": len(response.data),
            "page": response.page,
            "total_pages": response.total_pages,
            "elapsed_ms": round(elapsed * 1000, 2),
            "timestamp": time.time(),
        })

        return response