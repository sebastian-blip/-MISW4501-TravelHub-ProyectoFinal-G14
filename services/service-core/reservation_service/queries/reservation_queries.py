from dataclasses import dataclass, field
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import date, datetime


@dataclass
class UserResponse:
    id: UUID
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    user_type: str

    @classmethod
    def from_orm(cls, user) -> Optional["UserResponse"]:
        if user is None:
            return None
        return cls(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            user_type=user.user_type,
        )


@dataclass
class GuestResponse:
    id: UUID
    first_name: str
    last_name: str
    document_type: Optional[str]
    document_number: Optional[str]
    nationality: Optional[str]
    email: str
    is_primary: bool

    @classmethod
    def from_orm(cls, guest) -> "GuestResponse":
        return cls(
            id=guest.id,
            first_name=guest.first_name,
            last_name=guest.last_name,
            document_type=guest.document_type,
            document_number=guest.document_number,
            nationality=guest.nationality,
            email=guest.email,
            is_primary=guest.is_primary,
        )


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
class GetActivatedReservationsByUserQuery:
    user_id: UUID

@dataclass
class ListAllReservationsQuery:
    limit: int = 10
    offset: int = 0


@dataclass(kw_only=True)
class ReservationResponse:
    id: UUID
    user_id: Optional[UUID]
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
    user: Optional[UserResponse] = None
    reservation_guests: List[GuestResponse] = field(default_factory=list)

    @classmethod
    def from_orm(cls, reservation) -> "ReservationResponse":
        user = UserResponse.from_orm(reservation.user) if getattr(reservation, "user", None) else None
        guests = [
            GuestResponse.from_orm(g)
            for g in getattr(reservation, "reservation_guests", []) or []
        ]
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
            user=user,
            reservation_guests=guests,
        )


@dataclass
class ReservationListResponse:
    items: List[ReservationResponse]
    total: int
    limit: int
    offset: int
