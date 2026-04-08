from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from decimal import Decimal
from datetime import date


@dataclass
class CreateReservationCommand:
    user_id: UUID
    hotel_id: UUID
    room_type_id: UUID
    check_in: date
    check_out: date
    guests: int = 1
    base_price: Decimal = Decimal("0.00")
    taxes: Decimal = Decimal("0.00")
    discounts: Decimal = Decimal("0.00")
    total_price: Decimal = Decimal("0.00")
    currency_code: str = "USD"
    cart_id: Optional[UUID] = None
    cancellation_policy: Optional[str] = None
    special_requests: Optional[str] = None


@dataclass
class CreateReservationResponse:
    id: UUID
    user_id: UUID
    hotel_id: UUID
    confirmation_code: str
    status: str
    total_price: Decimal
    currency_code: str
    message: str


@dataclass
class UpdateReservationStatusCommand:
    reservation_id: UUID
    status: str  # pending, confirmed, cancelled, completed


@dataclass
class UpdateReservationStatusResponse:
    id: UUID
    previous_status: str
    new_status: str
    message: str
