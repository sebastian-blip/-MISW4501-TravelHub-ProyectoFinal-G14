"""Single shared PMS adapter instance for HTTP routes and Kafka consumers."""

from __future__ import annotations

import os

from domains.pms.adapters.factory import create_adapter
from domains.pms.ports.pms_port import PMSIntegrationPort

_cached: PMSIntegrationPort | None = None


def get_cached_pms_adapter() -> PMSIntegrationPort:
    global _cached
    if _cached is None:
        strategy = os.getenv("PMS_ADAPTER_STRATEGY", "pms")
        _cached = create_adapter(strategy)
    return _cached


def reset_cached_pms_adapter() -> None:
    global _cached
    _cached = None
