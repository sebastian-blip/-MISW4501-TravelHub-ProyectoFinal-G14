from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from domains.currency.currency_codes import fx_provider_code
from domains.currency.ports.currency_exchange_port import CurrencyExchangePort
from domains.currency.contracts import (
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
        base_fx = fx_provider_code(query.base_currency)
        quote_fx = fx_provider_code(query.quote_currency)
        key = f"{base_fx}:{quote_fx}"
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
            as_of_iso=rate_row.as_of_iso,
        )
