from typing import List

from mediatr import Mediator
from infrastructure.database import async_session_maker
from reservation_service.queries.reservation_queries import (
    GetReservationByIdQuery,
    GetReservationByCodeQuery,
    ListReservationsByUserQuery,
    ListAllReservationsQuery,
    ReservationResponse,
    ReservationListResponse,
)
from reservation_service.repository.reservation_repository import ReservationRepository


@Mediator.handler
class GetReservationByIdHandler:
    async def handle(self, query: GetReservationByIdQuery) -> ReservationResponse:
        async with async_session_maker() as session:
            repository = ReservationRepository(session)
            reservation = await repository.get_by_id(query.reservation_id)
            if reservation is None:
                raise ValueError(f"Reservación '{query.reservation_id}' no encontrada")
            return ReservationResponse.from_orm(reservation)


@Mediator.handler
class GetReservationByCodeHandler:
    async def handle(self, query: GetReservationByCodeQuery) -> ReservationResponse:
        async with async_session_maker() as session:
            repository = ReservationRepository(session)
            reservation = await repository.get_by_confirmation_code(query.confirmation_code)
            if reservation is None:
                raise ValueError(f"Reservación con código '{query.confirmation_code}' no encontrada")
            return ReservationResponse.from_orm(reservation)


@Mediator.handler
class ListReservationsByUserHandler:
    async def handle(self, query: ListReservationsByUserQuery) -> ReservationListResponse:
        async with async_session_maker() as session:
            repository = ReservationRepository(session)
            reservations = await repository.list_by_user_or_guest(
                query.user_id, limit=query.limit, offset=query.offset
            )
            items = [ReservationResponse.from_orm(r) for r in reservations]
            return ReservationListResponse(
                items=items,
                total=len(items),
                limit=query.limit,
                offset=query.offset,
            )


@Mediator.handler
class ListAllReservationsHandler:
    async def handle(self, query: ListAllReservationsQuery) -> ReservationListResponse:
        async with async_session_maker() as session:
            repository = ReservationRepository(session)
            reservations = await repository.list_all(limit=query.limit, offset=query.offset)
            items = [ReservationResponse.from_orm(r) for r in reservations]
            return ReservationListResponse(
                items=items,
                total=len(items),
                limit=query.limit,
                offset=query.offset,
            )
