"""Payment gateway — hexagonal HTTP entry-point (driving adapter)."""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.ports import PaymentPort
from app.adapters import create_adapter
from service_external.contracts.payment import PaymentIntentRequest

app = FastAPI(title="TravelHub Payment", version="0.1.0")
_adapter: PaymentPort | None = None

ADAPTER_STRATEGY = os.getenv("ADAPTER_STRATEGY", "gateway")


def get_adapter() -> PaymentPort:
    global _adapter
    if _adapter is None:
        _adapter = create_adapter(ADAPTER_STRATEGY)
    return _adapter


@app.get("/health")
def health():
    return {"status": "ok", "service": "payment", "strategy": ADAPTER_STRATEGY}


@app.get("/ready")
def ready():
    if os.getenv("TH_PAYMENT_SKIP_READY", "").lower() in ("1", "true", "yes"):
        return {"ready": True, "skipped": True}
    return {"ready": True}


class CreateIntentBody(BaseModel):
    amount_cents: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    customer_payment_token: str


@app.post("/v1/payment-intents")
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
