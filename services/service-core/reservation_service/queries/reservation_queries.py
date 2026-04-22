from dataclasses import dataclass
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import date, datetime


@dataclass
class GetReservationByIdQuery:
    reservation_id: UUID


@dataclass
class GetReservationByCodeQuery:
    confirmation_code: str


@dataclass
class ListReservationsByUserQuery:
    user_id: UUID
    limit: int = 10
    offset: int = 0


@dataclass
class ListAllReservationsQuery:
    limit: int = 10
    offset: int = 0


@dataclass
class ReservationResponse:
    id: UUID
    user_id: UUID
    hotel_id: UUID
    room_type_id: UUID
    cart_id: Optional[UUID]
    check_in: date
    check_out: date
    guests: int
    base_price: Decimal
    taxes: Decimal
    discounts: Decimal
    total_price: Decimal
    currency_code: str
    status: str
    cancellation_policy: Optional[str]
    special_requests: Optional[str]
    confirmation_code: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    @classmethod
    def from_orm(cls, reservation) -> "ReservationResponse":
        return cls(
            id=reservation.id,
            user_id=reservation.user_id,
            hotel_id=reservation.hotel_id,
            room_type_id=reservation.room_type_id,
            cart_id=reservation.cart_id,
            check_in=reservation.check_in,
            check_out=reservation.check_out,
            guests=reservation.guests,
            base_price=reservation.base_price,
            taxes=reservation.taxes,
            discounts=reservation.discounts,
            total_price=reservation.total_price,
            currency_code=reservation.currency_code,
            status=reservation.status,
            cancellation_policy=reservation.cancellation_policy,
            special_requests=reservation.special_requests,
            confirmation_code=reservation.confirmation_code,
            created_at=reservation.created_at,
            updated_at=reservation.updated_at,
        )


@dataclass
class ReservationListResponse:
    items: List[ReservationResponse]
    total: int
    limit: int
    offset: int
