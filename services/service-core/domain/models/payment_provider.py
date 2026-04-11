from sqlmodel import Field, SQLModel
from typing import Optional
import datetime
import uuid


class PaymentProvider(SQLModel, table=True):
    __tablename__ = "payment_providers"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=100)
    country_id: Optional[uuid.UUID] = Field(default=None)
    active: bool = Field(default=True)
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    def __str__(self):
        return self.name
