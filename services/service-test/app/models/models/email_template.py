from sqlmodel import Field, SQLModel
from typing import Optional
import datetime
import uuid


class EmailTemplate(SQLModel, table=True):
    __tablename__ = "email_templates"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=100, unique=True)
    subject: str = Field(max_length=255)
    body_html: str
    body_text: Optional[str] = Field(default=None)
    language: str = Field(default="es", max_length=5)
    active: bool = Field(default=True)
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    def __str__(self):
        return self.name
