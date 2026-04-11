from sqlmodel import Field, SQLModel
from typing import Optional
import uuid
import datetime


class RoomAmenity(SQLModel, table=True):
    __tablename__ = "room_amenities"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    room_type_id: uuid.UUID
    name: str = Field(max_length=100)
    icon: Optional[str] = Field(default=None, max_length=50)
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    def __str__(self):
        return self.name
