from sqlmodel import Field, SQLModel
from typing import Optional
import uuid
import datetime


class Country(SQLModel, table=True):
    __tablename__ = "countries"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    code: str = Field(max_length=3, unique=True)
    name: str = Field(max_length=100)
    currency_code: str = Field(max_length=3)
    active: bool = Field(default=True)
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    def __str__(self):
        return self.name
