from sqlmodel import Field, SQLModel
from typing import Optional
import datetime
import uuid


class ShoppingCart(SQLModel, table=True):
    __tablename__ = "shopping_carts"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID
    room_type_id: uuid.UUID
    check_in: datetime.date
    check_out: datetime.date
    guests: int = Field(default=1)
    hold_expires_at: datetime.datetime
    status: str = Field(default="active", max_length=50)
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    def __str__(self):
        return f"Cart {self.id}"
