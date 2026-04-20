"""`CurrencyExchangeAdapter` with injected `ExchangeClient` (no HTTP)."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from domains.currency.adapters.config import CurrencyExchangeSettings
from domains.currency.adapters.currency_exchange_adapter import CurrencyExchangeAdapter
from domains.currency.contracts import ConversionRequest, ExchangeRateQuery, RateRow
from resilience import CircuitBreaker


def test_get_rate_uses_cache_within_ttl():
    client = MagicMock()
    client.fetch_rate.return_value = RateRow(
        base_currency="USD",
        quote_currency="COP",
        rate=Decimal("2"),
        as_of_iso="2026-01-01T00:00:00+00:00",
    )
    settings = CurrencyExchangeSettings()
    settings.cache_ttl_seconds = 3600.0
    adapter = CurrencyExchangeAdapter(client=client, settings=settings)

    a = adapter.get_rate(ExchangeRateQuery(base_currency="USD", quote_currency="COP"))
    b = adapter.get_rate(ExchangeRateQuery(base_currency="USD", quote_currency="COP"))
    assert a.rate == Decimal("2")
    assert b.rate == Decimal("2")
    assert client.fetch_rate.call_count == 1


def test_get_rate_failure_opens_circuit_when_threshold_low():
    client = MagicMock()
    client.fetch_rate.side_effect = RuntimeError("boom")
    breaker = CircuitBreaker(failure_threshold=1)
    adapter = CurrencyExchangeAdapter(client=client, circuit_breaker=breaker)
    with pytest.raises(RuntimeError, match="boom"):
        adapter.get_rate(ExchangeRateQuery(base_currency="USD", quote_currency="EUR"))
    with pytest.raises(RuntimeError, match="fx_circuit_open"):
        adapter.get_rate(ExchangeRateQuery(base_currency="USD", quote_currency="EUR"))


def test_convert_delegates_to_get_rate():
    client = MagicMock()
    client.fetch_rate.return_value = RateRow(
        base_currency="USD",
        quote_currency="COP",
        rate=Decimal("10"),
        as_of_iso="2026-01-01T00:00:00+00:00",
    )
    adapter = CurrencyExchangeAdapter(client=client, settings=CurrencyExchangeSettings())
    out = adapter.convert(
        ConversionRequest(amount=Decimal("3"), from_currency="USD", to_currency="COP")
    )
    assert out.converted_amount == Decimal("30.00")
    assert out.rate == Decimal("10")
