from typing import List
from mediatr import Mediator

from poc1.hotel_service.queries.get_hotels_query import GetHotelsQuery, HotelResponse
from poc1.hotel_service.repository.hotel_repository import HotelRepository


@Mediator.handler
class GetHotelsQueryHandler:

    def __init__(self):
        self.repository = HotelRepository()

    async def handle(self, query: GetHotelsQuery) -> List[HotelResponse]:
        if query.city:
            hotels = await self.repository.get_by_city(query.city)
        else:
            hotels = await self.repository.get_all()

        return [HotelResponse.from_orm(h) for h in hotels]