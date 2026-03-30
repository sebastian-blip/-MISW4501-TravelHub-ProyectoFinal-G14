"""CDN/Storage — hexagonal HTTP entry-point (driving adapter)."""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.ports import StoragePort
from app.adapters import create_adapter
from service_external.contracts.storage import SignedUrlRequest

app = FastAPI(title="TravelHub CDN/Storage", version="0.1.0")
_adapter: StoragePort | None = None

ADAPTER_STRATEGY = os.getenv("ADAPTER_STRATEGY", "cdn")


def get_adapter() -> StoragePort:
    global _adapter
    if _adapter is None:
        _adapter = create_adapter(ADAPTER_STRATEGY)
    return _adapter


@app.get("/health")
def health():
    return {"status": "ok", "service": "cdn-storage", "strategy": ADAPTER_STRATEGY}


@app.get("/ready")
def ready():
    return {"ready": True}


class SignedUrlBody(BaseModel):
    asset_id: str
    expires_seconds: int = Field(default=3600, ge=60, le=86400)


@app.post("/v1/signed-urls")
def signed_url(body: SignedUrlBody):
    try:
        req = SignedUrlRequest(asset_id=body.asset_id, expires_seconds=body.expires_seconds)
        return get_adapter().create_signed_read_url(req).model_dump()
    except RuntimeError as e:
        if "circuit_open" in str(e):
            raise HTTPException(status_code=503, detail=str(e)) from e
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail="upstream_storage_error") from e
