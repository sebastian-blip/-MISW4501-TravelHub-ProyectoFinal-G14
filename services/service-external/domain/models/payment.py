import datetime
import uuid
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel


class Payment(SQLModel, table=True):
    __tablename__ = "payments"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    reservation_id: uuid.UUID
    provider_id: uuid.UUID
    amount: Decimal = Field(max_digits=10, decimal_places=2)
    currency_code: str = Field(default="USD", max_length=3)
    status: str = Field(default="pending", max_length=50)
    payment_token: Optional[str] = Field(default=None, max_length=255)
    provider_payment_id: Optional[str] = Field(default=None, max_length=255)
    failure_reason: Optional[str] = Field(default=None)
    refund_amount: Optional[Decimal] = Field(default=None, max_digits=10, decimal_places=2)
    refunded_at: Optional[datetime.datetime] = Field(default=None)
    processed_at: Optional[datetime.datetime] = Field(default=None)
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
