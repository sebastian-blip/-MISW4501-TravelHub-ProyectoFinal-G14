from typing import List
from mediatr import Mediator

from poc1.hotel_service.queries.get_reservation_query import GetReservationsQuery, ReservationResponse
from poc1.hotel_service.repository.reservation_repository import ReservationRepository

@Mediator.handler
class GetReservetionQueryHandler:

    def __init__(self):
        self.repository = ReservationRepository()

    async def handle(self, query: GetReservationsQuery) -> List[ReservationResponse]:
        repo = self.repository

        filters = {}

        if query.hotel_id:
            filters["hotel_id"] = query.hotel_id
        if query.room_id:
            filters["room_id"] = query.room_id
        if query.check_in:
            filters["check_in"] = query.check_in
        if query.check_out:
            filters["check_out"] = query.check_out
        if query.check_in and query.check_out:
            filters["contain_only"] = True

        reservations = await repo.list_by_filter(filters)

        return [ReservationResponse.from_orm(r) for r in reservations]

