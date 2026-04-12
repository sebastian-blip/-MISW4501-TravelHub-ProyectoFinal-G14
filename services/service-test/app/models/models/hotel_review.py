from sqlmodel import Field, SQLModel
from typing import Optional
from decimal import Decimal
import uuid
import datetime


class HotelReview(SQLModel, table=True):
    __tablename__ = "hotel_reviews"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hotel_id: uuid.UUID
    user_id: uuid.UUID
    reservation_id: Optional[uuid.UUID] = Field(default=None)
    overall_rating: Decimal = Field(max_digits=2, decimal_places=1)
    cleanliness_rating: Optional[Decimal] = Field(default=None, max_digits=2, decimal_places=1)
    service_rating: Optional[Decimal] = Field(default=None, max_digits=2, decimal_places=1)
    location_rating: Optional[Decimal] = Field(default=None, max_digits=2, decimal_places=1)
    value_rating: Optional[Decimal] = Field(default=None, max_digits=2, decimal_places=1)
    comment: Optional[str] = Field(default=None)
    response: Optional[str] = Field(default=None)
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    def __str__(self):
        return f"Review {self.id} - {self.overall_rating}"
