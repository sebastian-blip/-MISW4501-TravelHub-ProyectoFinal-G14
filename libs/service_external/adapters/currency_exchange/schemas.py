from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class RatesApiRow(BaseModel):
    base_currency: str
    quote_currency: str
    rate: Decimal
    as_of_iso: str
