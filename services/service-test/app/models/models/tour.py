from sqlmodel import Field, SQLModel
from typing import Optional
from decimal import Decimal
import datetime
import uuid


class Tour(SQLModel, table=True):
    __tablename__ = "tours"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None)
    country_id: uuid.UUID
    city: Optional[str] = Field(default=None, max_length=100)
    price: Decimal = Field(max_digits=10, decimal_places=2)
    currency_code: str = Field(default="USD", max_length=3)
    duration_hrs: Optional[int] = Field(default=None)
    active: bool = Field(default=True)
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    def __str__(self):
        return self.name
