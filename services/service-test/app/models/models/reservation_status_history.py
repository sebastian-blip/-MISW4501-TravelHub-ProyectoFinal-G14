from sqlmodel import Field, SQLModel
from typing import Optional
import datetime
import uuid


class ReservationStatusHistory(SQLModel, table=True):
    __tablename__ = "reservation_status_history"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    reservation_id: uuid.UUID
    previous_status: Optional[str] = Field(default=None, max_length=50)
    new_status: str = Field(max_length=50)
    changed_by: Optional[uuid.UUID] = Field(default=None)
    reason: Optional[str] = Field(default=None)
    ip_address: Optional[str] = Field(default=None, max_length=45)
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    def __str__(self):
        return f"{self.previous_status} -> {self.new_status}"
