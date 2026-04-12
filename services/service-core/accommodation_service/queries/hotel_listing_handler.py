from mediatr import Mediator
from typing import List

from infrastructure.database import async_session_maker
from accommodation_service.queries.accommodation_queries import (
    ListHotelsQuery,
    GetHotelAvailabilityQuery,
    ListCitiesQuery,
    HotelSummary,
    HotelAvailabilityResult,
    CityInfo,
)
from accommodation_service.repository.hotel_listing_repository import HotelListingRepository


@Mediator.handler
class ListHotelsHandler:
    """Handler para listar todos los hoteles con filtros opcionales"""

    async def handle(self, query: ListHotelsQuery) -> List[HotelSummary]:
        async with async_session_maker() as session:
            repository = HotelListingRepository(session)
            return await repository.list_hotels(
                city=query.city,
                country_id=query.country_id,
                min_stars=query.min_stars,
                max_stars=query.max_stars,
                min_rating=query.min_rating,
                active_only=query.active_only,
                limit=query.limit,
                offset=query.offset,
            )


@Mediator.handler
class GetHotelAvailabilityHandler:
    """Handler para ver disponibilidad de un hotel específico"""

    async def handle(self, query: GetHotelAvailabilityQuery) -> HotelAvailabilityResult:
        if query.check_out <= query.check_in:
            raise ValueError("check_out debe ser posterior a check_in")
        if query.guests < 1:
            raise ValueError("El número de huéspedes debe ser al menos 1")

        async with async_session_maker() as session:
            repository = HotelListingRepository(session)
            result = await repository.get_hotel_availability(
                hotel_id=query.hotel_id,
                check_in=query.check_in,
                check_out=query.check_out,
                guests=query.guests,
            )
            if result is None:
                raise ValueError(f"Hotel no encontrado o sin disponibilidad: {query.hotel_id}")
            return result


@Mediator.handler
class ListCitiesHandler:
    """Handler para listar ciudades con hoteles"""

    async def handle(self, query: ListCitiesQuery) -> List[CityInfo]:
        async with async_session_maker() as session:
            repository = HotelListingRepository(session)
            return await repository.list_cities(country_id=query.country_id)
