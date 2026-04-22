from mediatr import Mediator
from dataclasses import asdict
from infrastructure.database import async_session_maker
from accommodation_service.queries.accommodation_queries import (
    SearchAccommodationsQuery,
    ListHotelsResult
)
from accommodation_service.repository.accommodation_repository import AccommodationRepository
from typing import List


@Mediator.handler
class SearchAccommodationsHandler:

    async def handle(self, query: SearchAccommodationsQuery) -> ListHotelsResult:
        if query.check_out <= query.check_in:
            raise ValueError("check_out debe ser posterior a check_in")
        if query.guests < 1:
            raise ValueError("El nmero de huspedes debe ser al menos 1")

        async with async_session_maker() as session:
            repository = AccommodationRepository(session)
            return await repository.search(
               **asdict(query)
            )
