from sqlmodel import Field, SQLModel
from typing import Optional
from decimal import Decimal
import datetime
import uuid


class InventoryCalendar(SQLModel, table=True):
    __tablename__ = "inventory_calendar"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    room_type_id: uuid.UUID
    date: datetime.date
    available_units: int = Field(default=0)
    price_per_night: Decimal = Field(max_digits=10, decimal_places=2)
    currency_code: str = Field(default="USD", max_length=3)
    minimum_stay: int = Field(default=1)
    last_synced_at: Optional[datetime.datetime] = None
    def _utc_now_naive() -> datetime.datetime:
        return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

    created_at: datetime.datetime = Field(default_factory=_utc_now_naive)
    updated_at: datetime.datetime = Field(default_factory=_utc_now_naive)

    def __str__(self):
        return f"{self.room_type_id} - {self.date}"
