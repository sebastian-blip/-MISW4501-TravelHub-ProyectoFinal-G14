"""Tests for currency exchange mock adapter and HTTP `/currency/v1/rates`."""

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient

from domains.currency.adapters.mock_adapter import MockCurrencyAdapter
from domains.currency.contracts import ConversionRequest, ExchangeRateQuery
from main import app


class TestMockCurrencyAdapter:
    def test_get_rate_usd_cop(self):
        adapter = MockCurrencyAdapter()
        out = adapter.get_rate(ExchangeRateQuery(base_currency="USD", quote_currency="COP"))
        assert out.base_currency == "USD"
        assert out.quote_currency == "COP"
        assert out.rate == Decimal("4150.00")
        assert out.as_of_iso

    def test_get_rate_usd_eur(self):
        adapter = MockCurrencyAdapter()
        out = adapter.get_rate(ExchangeRateQuery(base_currency="usd", quote_currency="eur"))
        assert out.rate == Decimal("0.92")

    def test_get_rate_unknown_pair_defaults_to_one(self):
        adapter = MockCurrencyAdapter()
        out = adapter.get_rate(ExchangeRateQuery(base_currency="CHF", quote_currency="JPY"))
        assert out.rate == Decimal("1.00")

    def test_get_rate_usdc_uses_usd_table(self):
        adapter = MockCurrencyAdapter()
        out = adapter.get_rate(ExchangeRateQuery(base_currency="USDC", quote_currency="COP"))
        assert out.rate == Decimal("4150.00")

    def test_convert_applies_rate(self):
        adapter = MockCurrencyAdapter()
        result = adapter.convert(
            ConversionRequest(amount=Decimal("100.00"), from_currency="USD", to_currency="EUR")
        )
        assert result.from_currency == "USD"
        assert result.to_currency == "EUR"
        assert result.rate == Decimal("0.92")
        assert result.converted_amount == Decimal("92.00")
        assert result.as_of_iso


class TestCurrencyHTTP:
    def test_rates_usd_cop(self):
        with TestClient(app) as client:
            r = client.get("/currency/v1/rates", params={"base": "USD", "quote": "COP"})
        assert r.status_code == 200
        data = r.json()
        assert data["base_currency"] == "USD"
        assert data["quote_currency"] == "COP"
        assert Decimal(str(data["rate"])) == Decimal("4150.00")
        assert data.get("as_of_iso")

    def test_rates_lowercase_query_normalized(self):
        with TestClient(app) as client:
            r = client.get("/currency/v1/rates", params={"base": "usd", "quote": "eur"})
        assert r.status_code == 200
        data = r.json()
        assert data["base_currency"] == "USD"
        assert data["quote_currency"] == "EUR"
        assert Decimal(str(data["rate"])) == Decimal("0.92")

    def test_rates_invalid_currency_422(self):
        with TestClient(app) as client:
            r = client.get("/currency/v1/rates", params={"base": "XX", "quote": "USD"})
        assert r.status_code == 422

    def test_convert_endpoint_usd_cop(self):
        with TestClient(app) as client:
            r = client.post(
                "/currency/v1/convert",
                json={"amount": "10.00", "from_currency": "USD", "to_currency": "COP"},
            )
        assert r.status_code == 200
        data = r.json()
        assert data["from_currency"] == "USD"
        assert data["to_currency"] == "COP"
        assert Decimal(str(data["converted_amount"])) == Decimal("41500.00")
        assert data.get("as_of_iso")

    def test_convert_endpoint_usdc_cop(self):
        with TestClient(app) as client:
            r = client.post(
                "/currency/v1/convert",
                json={"amount": "2", "from_currency": "USDC", "to_currency": "COP"},
            )
        assert r.status_code == 200
        data = r.json()
        assert data["from_currency"] == "USDC"
        assert Decimal(str(data["converted_amount"])) == Decimal("8300.00")
        assert data.get("as_of_iso")
