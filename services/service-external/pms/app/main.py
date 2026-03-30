"""PMS integration — hexagonal HTTP entry-point (driving adapter)."""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException

from app.ports import PMSIntegrationPort
from app.adapters import create_adapter

app = FastAPI(title="TravelHub PMS", version="0.1.0")
_adapter: PMSIntegrationPort | None = None

ADAPTER_STRATEGY = os.getenv("ADAPTER_STRATEGY", "pms")


def get_adapter() -> PMSIntegrationPort:
    global _adapter
    if _adapter is None:
        _adapter = create_adapter(ADAPTER_STRATEGY)
    return _adapter


@app.get("/health")
def health():
    return {"status": "ok", "service": "pms", "strategy": ADAPTER_STRATEGY}


@app.get("/ready")
def ready():
    return {"ready": True}


@app.get("/v1/catalog/{hotel_external_id}")
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
