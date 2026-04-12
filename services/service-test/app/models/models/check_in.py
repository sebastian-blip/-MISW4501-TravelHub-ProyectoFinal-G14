from sqlmodel import Field, SQLModel
from typing import Optional
import datetime
import uuid


class CheckIn(SQLModel, table=True):
    __tablename__ = "check_ins"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    reservation_id: uuid.UUID = Field(unique=True)
    qr_code: str = Field(max_length=255, unique=True)
    room_number: Optional[str] = Field(default=None, max_length=20)
    checked_in_at: Optional[datetime.datetime] = Field(default=None)
    checked_out_at: Optional[datetime.datetime] = Field(default=None)
    status: str = Field(default="pending", max_length=50)
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    def __str__(self):
        return f"CheckIn {self.id}"
