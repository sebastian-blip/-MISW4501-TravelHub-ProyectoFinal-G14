from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import httpx

from domains.currency.adapters.config import CurrencyExchangeSettings
from domains.currency.currency_codes import fx_provider_code
from domains.currency.contracts import ExchangeRateQuery, RateRow


class ExchangeClient:
    """Fetches spot rates from Frankfurter (https://www.frankfurter.dev/docs/)."""

    def __init__(self, settings: CurrencyExchangeSettings | None = None) -> None:
        self._settings = settings or CurrencyExchangeSettings()

    def fetch_rate(self, query: ExchangeRateQuery) -> RateRow:
        base_fx = fx_provider_code(query.base_currency)
        quote_fx = fx_provider_code(query.quote_currency)
        now_iso = datetime.now(timezone.utc).isoformat()

        if base_fx == quote_fx:
            return RateRow(
                base_currency=query.base_currency,
                quote_currency=query.quote_currency,
                rate=Decimal("1"),
                as_of_iso=now_iso,
            )

        url = f"{self._settings.frankfurter_base_url}/v2/rate/{base_fx}/{quote_fx}"
        timeout = httpx.Timeout(self._settings.request_timeout_seconds)
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.get(url)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"fx_upstream_http_{e.response.status_code}") from e
        except httpx.RequestError as e:
            raise RuntimeError("fx_upstream_unreachable") from e

        try:
            rate = Decimal(str(payload["rate"]))
        except (KeyError, TypeError, ValueError) as e:
            raise RuntimeError("fx_upstream_invalid_payload") from e

        date_str = payload.get("date")
        if isinstance(date_str, str) and date_str:
            as_of_iso = f"{date_str}T12:00:00+00:00"
        else:
            as_of_iso = now_iso

        return RateRow(
            base_currency=query.base_currency,
            quote_currency=query.quote_currency,
            rate=rate,
            as_of_iso=as_of_iso,
        )
