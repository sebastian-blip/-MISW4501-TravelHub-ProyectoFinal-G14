"""HTTP routes for payment gateway (driving adapter)."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domains.payment.adapters import create_adapter
from app.domains.payment.ports import PaymentPort
from service_external.contracts.payment import PaymentIntentRequest

router = APIRouter()
_adapter: PaymentPort | None = None

STRATEGY = os.getenv("PAYMENT_ADAPTER_STRATEGY", "gateway")


def get_adapter() -> PaymentPort:
    global _adapter
    if _adapter is None:
        _adapter = create_adapter(STRATEGY)
    return _adapter


class CreateIntentBody(BaseModel):
    amount_cents: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    customer_payment_token: str


@router.post("/v1/payment-intents")
def create_payment_intent(body: CreateIntentBody):
    try:
        req = PaymentIntentRequest(
            amount_cents=body.amount_cents,
            currency=body.currency,
            customer_payment_token=body.customer_payment_token,
        )
        return get_adapter().create_payment_intent(req).model_dump()
    except RuntimeError as e:
        if "circuit_open" in str(e):
            raise HTTPException(status_code=503, detail=str(e)) from e
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail="upstream_payment_error") from e


def strategy_label() -> str:
    return STRATEGY
