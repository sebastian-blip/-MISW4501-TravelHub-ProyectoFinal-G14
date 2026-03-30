from __future__ import annotations

from pydantic import BaseModel, Field


class PaymentIntentRequest(BaseModel):
    amount_cents: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    customer_payment_token: str
    metadata: dict[str, str] = Field(default_factory=dict)


class PaymentIntentResult(BaseModel):
    id: str
    status: str
    client_secret: str | None = None


class RefundRequest(BaseModel):
    payment_intent_id: str
    amount_cents: int | None = None
    reason: str | None = None


class RefundResult(BaseModel):
    refund_id: str
    status: str


class TokenizeCardResult(BaseModel):
    payment_method_token: str
    brand: str | None = None
    last4: str | None = None
