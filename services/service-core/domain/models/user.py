from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, TYPE_CHECKING, List
import uuid

if TYPE_CHECKING:
    from domain.models.reservation import Reservation


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(max_length=255, unique=True)
    password_hash: str = Field(max_length=255)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)
    country_id: Optional[uuid.UUID] = Field(default=None)
    user_type: str = Field(max_length=50)  # 'traveler', 'hotel_admin', 'agency', 'admin'
    email_verified: bool = Field(default=False)
    mfa_enabled: bool = Field(default=False)
    active: bool = Field(default=True)

    reservations: List["Reservation"] = Relationship(back_populates="user")

    def __str__(self):
        return self.email
