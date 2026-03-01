from dataclasses import dataclass
from uuid import UUID
from datetime import date

@dataclass
class CreateReservationCommand:
    hotel_id: UUID
    room_id: UUID
    user_id: UUID
    check_in: date
    check_out: date

@dataclass
class ReservationCreatedResponse:
    id: UUID
    status: str