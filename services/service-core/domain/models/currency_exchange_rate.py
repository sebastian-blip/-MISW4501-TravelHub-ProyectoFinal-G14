from sqlmodel import Field, SQLModel
from decimal import Decimal
import datetime
import uuid


class CurrencyExchangeRate(SQLModel, table=True):
    __tablename__ = "currency_exchange_rates"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    from_currency: str = Field(max_length=3)
    to_currency: str = Field(max_length=3)
    rate: Decimal = Field(max_digits=15, decimal_places=6)
    fetched_at: datetime.datetime
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    def __str__(self):
        return f"{self.from_currency} -> {self.to_currency}"
