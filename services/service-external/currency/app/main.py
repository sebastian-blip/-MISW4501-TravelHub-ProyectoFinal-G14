"""Currency exchange — hexagonal HTTP entry-point (driving adapter)."""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException

from app.ports import CurrencyExchangePort
from app.adapters import create_adapter
from service_external.contracts.currency_exchange import ExchangeRateQuery

app = FastAPI(title="TravelHub Currency", version="0.1.0")
_adapter: CurrencyExchangePort | None = None

ADAPTER_STRATEGY = os.getenv("ADAPTER_STRATEGY", "exchange")


def get_adapter() -> CurrencyExchangePort:
    global _adapter
    if _adapter is None:
        _adapter = create_adapter(ADAPTER_STRATEGY)
    return _adapter


@app.get("/health")
def health():
    return {"status": "ok", "service": "currency", "strategy": ADAPTER_STRATEGY}


@app.get("/ready")
def ready():
    return {"ready": True}


@app.get("/v1/rates")
def get_rate(base: str, quote: str):
    try:
        q = ExchangeRateQuery(base_currency=base.upper()[:3], quote_currency=quote.upper()[:3])
        return get_adapter().get_rate(q).model_dump()
    except RuntimeError as e:
        if "circuit_open" in str(e):
            raise HTTPException(status_code=503, detail=str(e)) from e
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail="upstream_fx_error") from e
