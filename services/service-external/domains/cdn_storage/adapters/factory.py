from __future__ import annotations

from domains.cdn_storage.ports.storage_port import StoragePort

_STRATEGIES: dict[str, type] = {}


def _load_strategies() -> dict[str, type]:
    if _STRATEGIES:
        return _STRATEGIES
    from domains.cdn_storage.adapters.cdn_storage_adapter import CDNStorageAdapter
    from domains.cdn_storage.adapters.mock_adapter import MockStorageAdapter

    _STRATEGIES["cdn"] = CDNStorageAdapter
    _STRATEGIES["mock"] = MockStorageAdapter
    return _STRATEGIES


def create_adapter(strategy: str) -> StoragePort:
    strategies = _load_strategies()
    cls = strategies.get(strategy)
    if cls is None:
        available = ", ".join(sorted(strategies))
        raise ValueError(f"Unknown storage strategy '{strategy}'. Available: {available}")
    return cls()
