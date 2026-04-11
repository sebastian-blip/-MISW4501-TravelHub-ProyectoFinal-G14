from sqlmodel import Field, SQLModel
from typing import Optional
import uuid
import datetime


class HotelImage(SQLModel, table=True):
    __tablename__ = "hotel_images"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hotel_id: uuid.UUID
    url: str
    alt_text: Optional[str] = Field(default=None, max_length=255)
    sort_order: int = Field(default=0)
    image_type: str = Field(default="gallery", max_length=50)
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    def __str__(self):
        return f"Image {self.id}"
