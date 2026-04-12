from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Reservation(SQLModel, table=True):
    __tablename__ = "reservations"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(index=True)
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

    status: str = Field(default="pending", max_length=50)
    cancellation_policy: Optional[str] = Field(default=None, max_length=50)
    special_requests: Optional[str] = Field(default=None)
    confirmation_code: Optional[str] = Field(default=None, max_length=20, unique=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
