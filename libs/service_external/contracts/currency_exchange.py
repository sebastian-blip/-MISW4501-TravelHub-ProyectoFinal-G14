from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class ExchangeRateQuery(BaseModel):
    base_currency: str = Field(min_length=3, max_length=3)
    quote_currency: str = Field(min_length=3, max_length=3)


class ExchangeRateResult(BaseModel):
    base_currency: str
    quote_currency: str
    rate: Decimal
    as_of_iso: str


class ConversionRequest(BaseModel):
    amount: Decimal
    from_currency: str
    to_currency: str


class ConversionResult(BaseModel):
    amount: Decimal
    from_currency: str
    to_currency: str
    converted_amount: Decimal
    rate: Decimal
