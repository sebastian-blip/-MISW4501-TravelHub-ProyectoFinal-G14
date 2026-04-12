"""HTTP entry layer: one module per integration prefix.

`app.main` should only create FastAPI and call `mount_routes` here.
Each submodule wires FastAPI to `app.domains.*` (ports + adapter factory).
"""

from __future__ import annotations

from fastapi import FastAPI

from app.routes import cdn_storage, currency, maps, notification, payment, pms


def mount_routes(app: FastAPI) -> None:
    app.include_router(pms.router, prefix="/pms", tags=["pms"])
    app.include_router(payment.router, prefix="/payment", tags=["payment"])
    app.include_router(currency.router, prefix="/currency", tags=["currency"])
    app.include_router(cdn_storage.router, prefix="/cdn-storage", tags=["cdn-storage"])
    app.include_router(maps.router, prefix="/maps", tags=["maps"])
    app.include_router(notification.router, prefix="/notification", tags=["notification"])


def integration_strategies() -> dict[str, dict[str, str]]:
    """Per-integration adapter strategy (for /health)."""
    return {
        "pms": {"strategy": pms.strategy_label()},
        "payment": {"strategy": payment.strategy_label()},
        "currency": {"strategy": currency.strategy_label()},
        "cdn-storage": {"strategy": cdn_storage.strategy_label()},
        "maps": {"strategy": maps.strategy_label()},
        "notification": {"strategy": notification.strategy_label()},
    }
