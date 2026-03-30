from __future__ import annotations

from abc import ABC, abstractmethod

from service_external.contracts.currency_exchange import (
    ConversionRequest,
    ConversionResult,
    ExchangeRateQuery,
    ExchangeRateResult,
)


class CurrencyExchangePort(ABC):
    @abstractmethod
    def get_rate(self, query: ExchangeRateQuery) -> ExchangeRateResult:
        ...

    @abstractmethod
    def convert(self, request: ConversionRequest) -> ConversionResult:
        ...
