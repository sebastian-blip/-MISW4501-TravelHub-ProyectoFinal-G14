import datetime
import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel


class InventoryCalendar(SQLModel, table=True):
    __tablename__ = "inventory_calendar"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    room_type_id: uuid.UUID
    date: date
    available_units: int = Field(default=0)
    price_per_night: Decimal = Field(max_digits=10, decimal_places=2)
    currency_code: str = Field(default="USD", max_length=3)
    minimum_stay: int = Field(default=1)
    last_synced_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
