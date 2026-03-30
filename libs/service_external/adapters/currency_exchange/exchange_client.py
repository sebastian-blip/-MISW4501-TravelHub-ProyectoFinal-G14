from __future__ import annotations

import httpx

from service_external.adapters.currency_exchange.config import CurrencyExchangeSettings
from service_external.adapters.currency_exchange.schemas import RatesApiRow
from service_external.contracts.currency_exchange import ExchangeRateQuery


class ExchangeClient:
    def __init__(self, settings: CurrencyExchangeSettings | None = None):
        self._s = settings or CurrencyExchangeSettings()
        self._client = httpx.Client(
            base_url=self._s.base_url.rstrip("/"),
            timeout=self._s.timeout_seconds,
            verify=self._s.verify_tls,
            headers={"Authorization": f"Bearer {self._s.api_key}"} if self._s.api_key else {},
        )

    def close(self) -> None:
        self._client.close()

    def fetch_rate(self, query: ExchangeRateQuery) -> RatesApiRow:
        r = self._client.get(
            "/rates/latest",
            params={"base": query.base_currency.upper(), "quote": query.quote_currency.upper()},
        )
        r.raise_for_status()
        return RatesApiRow.model_validate(r.json())
