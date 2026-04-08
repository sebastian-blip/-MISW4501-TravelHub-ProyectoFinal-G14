from sqlmodel import Field, SQLModel
from typing import Optional
from decimal import Decimal
import datetime
import uuid


class RoomType(SQLModel, table=True):
    __tablename__ = "room_types"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hotel_id: uuid.UUID
    name: str = Field(max_length=100)
    description: Optional[str] = None
    base_price: Decimal = Field(max_digits=10, decimal_places=2)
    max_capacity: int = Field(default=2)
    bed_type: Optional[str] = Field(default=None, max_length=50)
    size_sqm: Optional[Decimal] = Field(default=None, max_digits=5, decimal_places=1)
    total_units: int = Field(default=1)
    active: bool = Field(default=True)
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    def __str__(self):
        return self.name
