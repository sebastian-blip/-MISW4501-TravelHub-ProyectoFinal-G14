from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from domains.currency.adapters.config import CurrencyExchangeSettings
from domains.currency.contracts import ExchangeRateQuery, RateRow


class ExchangeClient:
    _RATES: dict[str, Decimal] = {
        "USD:EUR": Decimal("0.92"),
        "USD:COP": Decimal("4150.00"),
        "EUR:USD": Decimal("1.09"),
        "EUR:COP": Decimal("4510.00"),
    }

    def __init__(self, settings: CurrencyExchangeSettings | None = None) -> None:
        self._settings = settings or CurrencyExchangeSettings()

    def fetch_rate(self, query: ExchangeRateQuery) -> RateRow:
        _ = self._settings
        key = f"{query.base_currency.upper()}:{query.quote_currency.upper()}"
        rate = self._RATES.get(key, Decimal("1.00"))
        return RateRow(
            base_currency=query.base_currency,
            quote_currency=query.quote_currency,
            rate=rate,
            as_of_iso=datetime.now(timezone.utc).isoformat(),
        )
