from sqlmodel import Field, SQLModel
from typing import Optional
from decimal import Decimal
import datetime
import uuid


class SpecialOffer(SQLModel, table=True):
    __tablename__ = "special_offers"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hotel_id: uuid.UUID
    room_type_id: Optional[uuid.UUID] = Field(default=None)
    title: str = Field(max_length=255)
    description: Optional[str] = Field(default=None)
    discount_pct: Decimal = Field(max_digits=5, decimal_places=2)
    valid_from: datetime.date
    valid_to: datetime.date
    active: bool = Field(default=True)
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    def __str__(self):
        return self.title
