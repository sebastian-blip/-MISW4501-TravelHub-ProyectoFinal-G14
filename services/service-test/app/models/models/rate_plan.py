from sqlmodel import Field, SQLModel
from typing import Optional
from decimal import Decimal
import datetime
import uuid


class RatePlan(SQLModel, table=True):
    __tablename__ = "rate_plans"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hotel_id: uuid.UUID
    name: str = Field(max_length=100)
    discount_pct: Decimal = Field(default=Decimal("0"), max_digits=5, decimal_places=2)
    valid_from: Optional[datetime.date] = Field(default=None)
    valid_to: Optional[datetime.date] = Field(default=None)
    minimum_stay: int = Field(default=1)
    refundable: bool = Field(default=True)
    active: bool = Field(default=True)
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    def __str__(self):
        return self.name
