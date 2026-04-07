from sqlmodel import Field, SQLModel
from typing import Optional
from decimal import Decimal
import datetime
import uuid


class Hotel(SQLModel, table=True):
    __tablename__ = "hotels"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255)
    description: Optional[str] = None
    address: str
    city: str = Field(max_length=100)
    country_id: uuid.UUID
    latitude: Optional[Decimal] = Field(default=None, max_digits=10, decimal_places=8)
    longitude: Optional[Decimal] = Field(default=None, max_digits=11, decimal_places=8)
    phone: Optional[str] = Field(default=None, max_length=20)
    email: Optional[str] = Field(default=None, max_length=255)
    stars: int = Field(default=3)
    rating: Optional[Decimal] = Field(default=None, max_digits=2, decimal_places=1)
    total_reviews: int = Field(default=0)
    check_in_time: datetime.time = Field(default=datetime.time(15, 0))
    check_out_time: datetime.time = Field(default=datetime.time(11, 0))
    owner_user_id: Optional[uuid.UUID] = Field(default=None)
    pms_provider: Optional[str] = Field(default=None, max_length=100)
    pms_hotel_code: Optional[str] = Field(default=None, max_length=100)
    active: bool = Field(default=True)
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    def __str__(self):
        return self.name
