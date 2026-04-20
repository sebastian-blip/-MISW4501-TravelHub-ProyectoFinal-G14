"""Frankfurter HTTP client (mocked)."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from domains.currency.adapters.exchange_client import ExchangeClient
from domains.currency.contracts import ExchangeRateQuery


def test_exchange_client_same_currency_no_http():
    with patch("domains.currency.adapters.exchange_client.httpx.Client") as client_cls:
        row = ExchangeClient().fetch_rate(ExchangeRateQuery(base_currency="USD", quote_currency="USD"))
    client_cls.assert_not_called()
    assert row.rate == Decimal("1")
    assert row.base_currency == "USD"


def test_exchange_client_usdc_to_usd_no_http():
    with patch("domains.currency.adapters.exchange_client.httpx.Client") as client_cls:
        row = ExchangeClient().fetch_rate(ExchangeRateQuery(base_currency="USDC", quote_currency="USD"))
    client_cls.assert_not_called()
    assert row.rate == Decimal("1")


def test_exchange_client_parses_frankfurter_json():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "date": "2026-01-02",
        "base": "USD",
        "quote": "COP",
        "rate": 4000.25,
    }
    mock_http = MagicMock()
    mock_http.get.return_value = mock_response

    with patch("domains.currency.adapters.exchange_client.httpx.Client") as client_cls:
        client_cls.return_value.__enter__.return_value = mock_http
        row = ExchangeClient().fetch_rate(ExchangeRateQuery(base_currency="USD", quote_currency="COP"))

    mock_http.get.assert_called_once()
    assert row.rate == Decimal("4000.25")
    assert row.quote_currency == "COP"
    assert "2026-01-02T12:00:00+00:00" == row.as_of_iso


def test_exchange_client_http_error_maps_to_runtime():
    import httpx

    from domains.currency.adapters.exchange_client import ExchangeClient
    from domains.currency.contracts import ExchangeRateQuery

    err = httpx.HTTPStatusError(
        "nope", request=MagicMock(), response=MagicMock(status_code=404)
    )
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = err
    mock_http = MagicMock()
    mock_http.get.return_value = mock_response

    with patch("domains.currency.adapters.exchange_client.httpx.Client") as client_cls:
        client_cls.return_value.__enter__.return_value = mock_http
        with pytest.raises(RuntimeError, match="fx_upstream_http_404"):
            ExchangeClient().fetch_rate(ExchangeRateQuery(base_currency="USD", quote_currency="COP"))


def test_exchange_client_request_error():
    import httpx

    from domains.currency.adapters.exchange_client import ExchangeClient
    from domains.currency.contracts import ExchangeRateQuery

    mock_http = MagicMock()
    mock_http.get.side_effect = httpx.RequestError("offline", request=MagicMock())

    with patch("domains.currency.adapters.exchange_client.httpx.Client") as client_cls:
        client_cls.return_value.__enter__.return_value = mock_http
        with pytest.raises(RuntimeError, match="fx_upstream_unreachable"):
            ExchangeClient().fetch_rate(ExchangeRateQuery(base_currency="USD", quote_currency="COP"))


def test_exchange_client_invalid_payload():
    from domains.currency.adapters.exchange_client import ExchangeClient
    from domains.currency.contracts import ExchangeRateQuery

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"date": "2026-01-01"}
    mock_http = MagicMock()
    mock_http.get.return_value = mock_response

    with patch("domains.currency.adapters.exchange_client.httpx.Client") as client_cls:
        client_cls.return_value.__enter__.return_value = mock_http
        with pytest.raises(RuntimeError, match="fx_upstream_invalid_payload"):
            ExchangeClient().fetch_rate(ExchangeRateQuery(base_currency="USD", quote_currency="COP"))


def test_exchange_client_missing_date_uses_now():
    from domains.currency.adapters.exchange_client import ExchangeClient
    from domains.currency.contracts import ExchangeRateQuery

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"base": "USD", "quote": "COP", "rate": 1.5}
    mock_http = MagicMock()
    mock_http.get.return_value = mock_response

    with patch("domains.currency.adapters.exchange_client.httpx.Client") as client_cls:
        client_cls.return_value.__enter__.return_value = mock_http
        row = ExchangeClient().fetch_rate(ExchangeRateQuery(base_currency="USD", quote_currency="COP"))
    assert row.rate == Decimal("1.5")
    assert "T" in row.as_of_iso
