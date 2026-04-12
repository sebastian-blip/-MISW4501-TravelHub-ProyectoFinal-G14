from __future__ import annotations

from domains.payment.ports.payment_port import PaymentPort

_STRATEGIES: dict[str, type] = {}


def _load_strategies() -> dict[str, type]:
    if _STRATEGIES:
        return _STRATEGIES
    from domains.payment.adapters.payment_gateway_adapter import PaymentGatewayAdapter
    from domains.payment.adapters.mock_adapter import MockPaymentAdapter

    _STRATEGIES["gateway"] = PaymentGatewayAdapter
    _STRATEGIES["mock"] = MockPaymentAdapter
    return _STRATEGIES


def create_adapter(strategy: str) -> PaymentPort:
    strategies = _load_strategies()
    cls = strategies.get(strategy)
    if cls is None:
        available = ", ".join(sorted(strategies))
        raise ValueError(f"Unknown payment strategy '{strategy}'. Available: {available}")
    return cls()
