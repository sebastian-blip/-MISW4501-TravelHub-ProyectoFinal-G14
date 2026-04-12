from __future__ import annotations

from abc import ABC, abstractmethod

from domains.currency.contracts import (
    ConversionRequest,
    ConversionResult,
    ExchangeRateQuery,
    ExchangeRateResult,
)


class CurrencyExchangePort(ABC):
    """Contract that any currency exchange adapter must implement."""

    @abstractmethod
    def get_rate(self, query: ExchangeRateQuery) -> ExchangeRateResult: ...

    @abstractmethod
    def convert(self, request: ConversionRequest) -> ConversionResult: ...
