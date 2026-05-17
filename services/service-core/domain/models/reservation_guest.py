from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, TYPE_CHECKING
import datetime
import uuid

if TYPE_CHECKING:
    from domain.models.reservation import Reservation


class ReservationGuest(SQLModel, table=True):
    __tablename__ = "reservation_guests"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    reservation_id: uuid.UUID = Field(foreign_key="reservations.id")
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    document_type: Optional[str] = Field(default=None, max_length=50)
    document_number: Optional[str] = Field(default=None, max_length=50)
    nationality: Optional[str] = Field(default=None, max_length=3)
    email: str = Field(default="", max_length=255)
    is_primary: bool = Field(default=False)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    reservation: Optional["Reservation"] = Relationship(back_populates="reservation_guests")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
