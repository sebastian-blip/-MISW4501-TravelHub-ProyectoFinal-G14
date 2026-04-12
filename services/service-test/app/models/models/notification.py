from sqlmodel import Field, SQLModel
from typing import Optional
import datetime
import uuid


class Notification(SQLModel, table=True):
    __tablename__ = "notifications"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID
    type: str = Field(max_length=50)
    title: str = Field(max_length=255)
    body: str
    related_entity: Optional[str] = Field(default=None, max_length=50)
    entity_id: Optional[uuid.UUID] = Field(default=None)
    sent_at: Optional[datetime.datetime] = Field(default=None)
    read_at: Optional[datetime.datetime] = Field(default=None)
    status: str = Field(default="pending", max_length=50)
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    def __str__(self):
        return self.title
