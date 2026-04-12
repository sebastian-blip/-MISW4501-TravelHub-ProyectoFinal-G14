from __future__ import annotations

from app.domains.currency.ports.currency_exchange_port import CurrencyExchangePort

_STRATEGIES: dict[str, type] = {}


def _load_strategies() -> dict[str, type]:
    if _STRATEGIES:
        return _STRATEGIES
    from app.domains.currency.adapters.currency_exchange_adapter import CurrencyExchangeAdapter
    from app.domains.currency.adapters.mock_adapter import MockCurrencyAdapter

    _STRATEGIES["exchange"] = CurrencyExchangeAdapter
    _STRATEGIES["mock"] = MockCurrencyAdapter
    return _STRATEGIES


def create_adapter(strategy: str) -> CurrencyExchangePort:
    strategies = _load_strategies()
    cls = strategies.get(strategy)
    if cls is None:
        available = ", ".join(sorted(strategies))
        raise ValueError(f"Unknown currency strategy '{strategy}'. Available: {available}")
    return cls()
