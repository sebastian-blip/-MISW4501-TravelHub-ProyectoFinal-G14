from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from domains.currency.currency_codes import validate_display_currency


class ExchangeRateQuery(BaseModel):
    base_currency: str
    quote_currency: str

    @field_validator("base_currency", "quote_currency", mode="before")
    @classmethod
    def _strip_ccy(cls, v: object) -> str:
        return str(v).strip()

    @field_validator("base_currency", "quote_currency")
    @classmethod
    def _validate_ccy(cls, v: str) -> str:
        return validate_display_currency(v)


class ExchangeRateResult(BaseModel):
    base_currency: str
    quote_currency: str
    rate: Decimal
    as_of_iso: str


class ConversionRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    from_currency: str
    to_currency: str

    @field_validator("from_currency", "to_currency", mode="before")
    @classmethod
    def _strip_conv_ccy(cls, v: object) -> str:
        return str(v).strip()

    @field_validator("from_currency", "to_currency")
    @classmethod
    def _validate_conv_ccy(cls, v: str) -> str:
        return validate_display_currency(v)


class ConversionResult(BaseModel):
    amount: Decimal
    from_currency: str
    to_currency: str
    converted_amount: Decimal
    rate: Decimal
    as_of_iso: str


class RateRow(BaseModel):
    base_currency: str
    quote_currency: str
    rate: Decimal
    as_of_iso: str
