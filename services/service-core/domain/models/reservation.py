from datetime import date, datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING, List
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from domain.models.user import User
    from domain.models.reservation_guest import ReservationGuest


class Reservation(SQLModel, table=True):
    __tablename__ = "reservations"
    
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: Optional[UUID] = Field(default=None, index=True, foreign_key="users.id")
    hotel_id: UUID = Field(index=True)
    room_type_id: UUID = Field(index=True)
    cart_id: Optional[UUID] = Field(default=None, index=True)
    
    check_in: date
    check_out: date
    guests: int = Field(default=1)
    
    base_price: Decimal = Field(max_digits=10, decimal_places=2)
    taxes: Decimal = Field(default=Decimal("0"), max_digits=10, decimal_places=2)
    discounts: Decimal = Field(default=Decimal("0"), max_digits=10, decimal_places=2)
    total_price: Decimal = Field(max_digits=10, decimal_places=2)
    currency_code: str = Field(default="USD", max_length=3)
    
    status: str = Field(default="pending", max_length=50)  # pending, confirmed, cancelled, completed
    cancellation_policy: Optional[str] = Field(default=None, max_length=50)
    special_requests: Optional[str] = Field(default=None)
    confirmation_code: Optional[str] = Field(default=None, max_length=20, unique=True)
    user_guest_id : Optional[UUID] = Field(default=None, index=True)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    user: Optional["User"] = Relationship(back_populates="reservations")
    reservation_guests: List["ReservationGuest"] = Relationship(back_populates="reservation")
