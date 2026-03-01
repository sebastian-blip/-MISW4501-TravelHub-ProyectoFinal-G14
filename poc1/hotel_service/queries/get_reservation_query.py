from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from datetime import date


@dataclass
class ReservationResponse:
    id: UUID
    hotel_id: UUID
    room_id: UUID
    user_id: UUID
    check_in: date
    check_out: date
    status: str

    @classmethod
    def from_orm(cls, reservation) -> "ReservationResponse":

        check_in = getattr(reservation, "check_in", None)
        check_out = getattr(reservation, "check_out", None)

        if hasattr(check_in, "date"):
            check_in = check_in.date()
        if hasattr(check_out, "date"):
            check_out = check_out.date()

        return cls(
            id=reservation.id,
            hotel_id=reservation.hotel_id,
            room_id=reservation.room_id,
            user_id=reservation.user_id,
            check_in=check_in,
            check_out=check_out,
            status=reservation.status,
        )


@dataclass
class GetReservationsQuery:
    hotel_id: Optional[UUID] = None
    room_id: Optional[UUID] = None
    check_in: Optional[date] = None
    check_out: Optional[date] = None



