from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from uuid import UUID
from datetime import date

from mediatr import Mediator
from poc1.hotel_service.queries.get_reservation_query import GetReservationsQuery, ReservationResponse
import poc1.hotel_service.queries.get_reservation_handler  # Esto registra el handler

router = APIRouter(prefix="/reservations", tags=["Reservations"])


def get_mediator() -> Mediator:
    return Mediator()

@router.get("", response_model=List[ReservationResponse])
async def get_reservations(
    hotel_id: Optional[UUID] = Query(None),
    room_id: Optional[UUID] = Query(None),
    check_in: Optional[date] = Query(None),
    check_out: Optional[date] = Query(None),
    mediator: Mediator = Depends(get_mediator)
):
    query = GetReservationsQuery(
        hotel_id=hotel_id,
        room_id=room_id,
        check_in=check_in,
        check_out=check_out,
    )
    return await mediator.send(query)