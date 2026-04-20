"""HTTP routes for currency exchange (driving adapter)."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from domains.currency.adapters import create_adapter
from domains.currency.ports import CurrencyExchangePort
from domains.currency.contracts import ConversionRequest, ExchangeRateQuery

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
        q = ExchangeRateQuery(base_currency=base, quote_currency=quote)
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail=e.errors(include_url=False, include_context=False),
        ) from e
    try:
        return get_adapter().get_rate(q).model_dump()
    except RuntimeError as e:
        if "circuit_open" in str(e):
            raise HTTPException(status_code=503, detail=str(e)) from e
        raise HTTPException(status_code=502, detail="upstream_fx_error") from e
    except Exception:
        raise HTTPException(status_code=502, detail="upstream_fx_error")


@router.post("/v1/convert")
def convert(body: ConversionRequest):
    try:
        return get_adapter().convert(body).model_dump()
    except RuntimeError as e:
        if "circuit_open" in str(e):
            raise HTTPException(status_code=503, detail=str(e)) from e
        raise HTTPException(status_code=502, detail="upstream_fx_error") from e
    except Exception:
        raise HTTPException(status_code=502, detail="upstream_fx_error")


def strategy_label() -> str:
    return STRATEGY
