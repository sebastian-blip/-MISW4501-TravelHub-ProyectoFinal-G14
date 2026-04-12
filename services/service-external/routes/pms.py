"""HTTP routes for PMS integration (driving adapter)."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException

from domains.pms.adapters import create_adapter
from domains.pms.ports import PMSIntegrationPort

router = APIRouter()
_adapter: PMSIntegrationPort | None = None

STRATEGY = os.getenv("PMS_ADAPTER_STRATEGY", "pms")


def get_adapter() -> PMSIntegrationPort:
    global _adapter
    if _adapter is None:
        _adapter = create_adapter(STRATEGY)
    return _adapter


@router.get("/v1/catalog/{hotel_external_id}")
def get_catalog(hotel_external_id: str):
    try:
        snap = get_adapter().fetch_catalog_snapshot(hotel_external_id)
        return snap.model_dump()
    except RuntimeError as e:
        if "circuit_open" in str(e):
            raise HTTPException(status_code=503, detail=str(e)) from e
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail="upstream_pms_error") from e


def strategy_label() -> str:
    return STRATEGY
