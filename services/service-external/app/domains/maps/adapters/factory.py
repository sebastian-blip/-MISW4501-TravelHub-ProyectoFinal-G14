from __future__ import annotations

from app.domains.maps.ports.location_port import LocationPort

_STRATEGIES: dict[str, type] = {}


def _load_strategies() -> dict[str, type]:
    if _STRATEGIES:
        return _STRATEGIES
    from app.domains.maps.adapters.maps_location_adapter import MapsLocationAdapter
    from app.domains.maps.adapters.mock_adapter import MockLocationAdapter

    _STRATEGIES["maps"] = MapsLocationAdapter
    _STRATEGIES["mock"] = MockLocationAdapter
    return _STRATEGIES


def create_adapter(strategy: str) -> LocationPort:
    strategies = _load_strategies()
    cls = strategies.get(strategy)
    if cls is None:
        available = ", ".join(sorted(strategies))
        raise ValueError(f"Unknown maps strategy '{strategy}'. Available: {available}")
    return cls()
