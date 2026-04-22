from sqlmodel import Field, SQLModel
from typing import Optional
from decimal import Decimal
import datetime
import uuid


class PaymentTransaction(SQLModel, table=True):
    __tablename__ = "payment_transactions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    payment_id: uuid.UUID
    type: str = Field(max_length=50)
    amount: Decimal = Field(max_digits=10, decimal_places=2)
    status: str = Field(max_length=50)
    provider_tx_id: Optional[str] = Field(default=None, max_length=255)
    fraud_score: Optional[Decimal] = Field(default=None, max_digits=5, decimal_places=2)
    three_ds_verified: bool = Field(default=False)
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    def __str__(self):
        return f"Transaction {self.id}"
