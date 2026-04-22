from dataclasses import dataclass, field
from typing import Optional, Any
from uuid import UUID
from decimal import Decimal
from datetime import date


@dataclass
class CreateReservationCommand:
    hotel_id: UUID
    room_type_id: UUID
    check_in: date
    check_out: date
    #primary_guest: Any  # PrimaryGuestRequest
    #payment: Any  # PaymentRequest
    guests: int = 1
    base_price: Decimal = Decimal("0.00")
    taxes: Decimal = Decimal("0.00")
    discounts: Decimal = Decimal("0.00")
    total_price: Decimal = Decimal("0.00")
    currency_code: str = "USD"
    user_id: Optional[UUID] = None
    user_guest_id: Optional[UUID] = None
    cart_id: Optional[UUID] = None
    cancellation_policy: Optional[str] = None
    special_requests: Optional[str] = None


@dataclass
class HotelInfo:
    id: UUID
    name: str
    description: Optional[str]
    address: str
    city: str
    stars: int
    rating: Optional[Decimal]


@dataclass
class RoomTypeInfo:
    id: UUID
    name: str
    description: Optional[str]
    max_capacity: int
    bed_type: Optional[str]
    size_sqm: Optional[Decimal]


@dataclass
class PricingDetails:
    nights: int
    guests: int
    price_per_night: Decimal
    subtotal: Decimal  # price_per_night * nights
    taxes: Decimal
    discounts: Decimal
    total: Decimal
    currency_code: str


@dataclass
class CreateReservationResponse:
    id: UUID
    user_id: Optional[UUID]
    confirmation_code: str
    status: str
    message: str
    hotel: HotelInfo
    room_type: RoomTypeInfo
    pricing: PricingDetails
    check_in: date
    check_out: date


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
