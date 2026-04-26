from sqlmodel import Field, SQLModel
from typing import Optional
import datetime
import uuid


class ReservationGuest(SQLModel, table=True):
    __tablename__ = "reservation_guests"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    reservation_id: uuid.UUID
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    document_type: Optional[str] = Field(default=None, max_length=50)
    document_number: Optional[str] = Field(default=None, max_length=50)
    nationality: Optional[str] = Field(default=None, max_length=3)
    email: str = Field(default="", max_length=255)
    is_primary: bool = Field(default=False)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
