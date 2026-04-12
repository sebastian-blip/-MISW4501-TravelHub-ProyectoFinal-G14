"""HTTP routes for currency exchange (driving adapter)."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException

from app.domains.currency.adapters import create_adapter
from app.domains.currency.ports import CurrencyExchangePort
from service_external.contracts.currency_exchange import ExchangeRateQuery

router = APIRouter()
_adapter: CurrencyExchangePort | None = None

STRATEGY = os.getenv("CURRENCY_ADAPTER_STRATEGY", "exchange")


def get_adapter() -> CurrencyExchangePort:
    global _adapter
    if _adapter is None:
        _adapter = create_adapter(STRATEGY)
    return _adapter


@router.get("/v1/rates")
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


def strategy_label() -> str:
    return STRATEGY
