from sqlmodel import Field, SQLModel
from typing import Optional
import datetime
import uuid


class UserSession(SQLModel, table=True):
    __tablename__ = "user_sessions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID
    token: str = Field(max_length=500, unique=True)
    ip_address: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = Field(default=None)
    expires_at: datetime.datetime
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    def __str__(self):
        return f"Session {self.id}"
