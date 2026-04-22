from __future__ import annotations

import time
from decimal import Decimal

from domains.currency.ports.currency_exchange_port import CurrencyExchangePort
from domains.currency.adapters.config import CurrencyExchangeSettings
from domains.currency.adapters.exchange_client import ExchangeClient
from domains.currency.contracts import (
    ConversionRequest,
    ConversionResult,
    ExchangeRateQuery,
    ExchangeRateResult,
)
from resilience import CircuitBreaker, retry_with_backoff


class CurrencyExchangeAdapter(CurrencyExchangePort):
    """Driven adapter — calls the FX provider via ExchangeClient."""

    def __init__(
        self,
        client: ExchangeClient | None = None,
        settings: CurrencyExchangeSettings | None = None,
        circuit_breaker: CircuitBreaker | None = None,
    ):
        self._settings = settings or CurrencyExchangeSettings()
        self._client = client or ExchangeClient(self._settings)
        self._breaker = circuit_breaker or CircuitBreaker(failure_threshold=12)
        self._cache: dict[str, tuple[float, ExchangeRateResult]] = {}

    def _cache_key(self, query: ExchangeRateQuery) -> str:
        return f"{query.base_currency.upper()}:{query.quote_currency.upper()}"

    def _run(self, fn):
        if not self._breaker.allow():
            raise RuntimeError("fx_circuit_open")
        try:
            out = retry_with_backoff(fn, max_attempts=3)
            self._breaker.record_success()
            return out
        except Exception:
            self._breaker.record_failure()
            raise

    def get_rate(self, query: ExchangeRateQuery) -> ExchangeRateResult:
        key = self._cache_key(query)
        now = time.monotonic()
        hit = self._cache.get(key)
        if hit and now - hit[0] < self._settings.cache_ttl_seconds:
            return hit[1]

        def _call():
            row = self._client.fetch_rate(query)
            return ExchangeRateResult(
                base_currency=row.base_currency,
                quote_currency=row.quote_currency,
                rate=row.rate,
                as_of_iso=row.as_of_iso,
            )

        result = self._run(_call)
        self._cache[key] = (now, result)
        return result

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
