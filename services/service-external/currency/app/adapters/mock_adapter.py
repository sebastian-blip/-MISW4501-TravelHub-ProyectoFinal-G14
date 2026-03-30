from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from app.ports.currency_exchange_port import CurrencyExchangePort
from service_external.contracts.currency_exchange import (
    ConversionRequest,
    ConversionResult,
    ExchangeRateQuery,
    ExchangeRateResult,
)

_MOCK_RATES: dict[str, Decimal] = {
    "USD:EUR": Decimal("0.92"),
    "USD:COP": Decimal("4150.00"),
    "EUR:USD": Decimal("1.09"),
    "EUR:COP": Decimal("4510.00"),
}


class MockCurrencyAdapter(CurrencyExchangePort):
    """In-memory stub with fixed rates for local development and testing."""

    def get_rate(self, query: ExchangeRateQuery) -> ExchangeRateResult:
        key = f"{query.base_currency.upper()}:{query.quote_currency.upper()}"
        rate = _MOCK_RATES.get(key, Decimal("1.00"))
        return ExchangeRateResult(
            base_currency=query.base_currency,
            quote_currency=query.quote_currency,
            rate=rate,
            as_of_iso=datetime.now(timezone.utc).isoformat(),
        )

    def convert(self, request: ConversionRequest) -> ConversionResult:
        rate_row = self.get_rate(
            ExchangeRateQuery(base_currency=request.from_currency, quote_currency=request.to_currency)
        )
        converted = (request.amount * rate_row.rate).quantize(Decimal("0.01"))
        return ConversionResult(
            amount=request.amount,
            from_currency=request.from_currency,
            to_currency=request.to_currency,
            converted_amount=converted,
            rate=rate_row.rate,
        )
