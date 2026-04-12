from __future__ import annotations

from domains.pms.ports.pms_port import PMSIntegrationPort

_STRATEGIES: dict[str, type] = {}


def _load_strategies() -> dict[str, type]:
    if _STRATEGIES:
        return _STRATEGIES
    from domains.pms.adapters.pms_adapter import PMSAdapter
    from domains.pms.adapters.mock_adapter import MockPMSAdapter

    _STRATEGIES["pms"] = PMSAdapter
    _STRATEGIES["mock"] = MockPMSAdapter
    return _STRATEGIES


def create_adapter(strategy: str) -> PMSIntegrationPort:
    strategies = _load_strategies()
    cls = strategies.get(strategy)
    if cls is None:
        available = ", ".join(sorted(strategies))
        raise ValueError(f"Unknown PMS strategy '{strategy}'. Available: {available}")
    return cls()
