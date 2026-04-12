from sqlmodel import Field, SQLModel
from typing import Optional
import datetime
import uuid


class UserPreference(SQLModel, table=True):
    __tablename__ = "user_preferences"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(unique=True)
    preferred_currency: str = Field(default="USD", max_length=3)
    preferred_language: str = Field(default="es", max_length=5)
    notifications_email: bool = Field(default=True)
    notifications_push: bool = Field(default=True)
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    def __str__(self):
        return f"Preferences for user {self.user_id}"
