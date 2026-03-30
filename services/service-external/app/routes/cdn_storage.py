"""HTTP routes for CDN / signed URLs (driving adapter)."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domains.cdn_storage.adapters import create_adapter
from app.domains.cdn_storage.ports import StoragePort
from service_external.contracts.storage import SignedUrlRequest

router = APIRouter()
_adapter: StoragePort | None = None

STRATEGY = os.getenv("CDN_STORAGE_ADAPTER_STRATEGY", "cdn")


def get_adapter() -> StoragePort:
    global _adapter
    if _adapter is None:
        _adapter = create_adapter(STRATEGY)
    return _adapter


class SignedUrlBody(BaseModel):
    asset_id: str
    expires_seconds: int = Field(default=3600, ge=60, le=86400)


@router.post("/v1/signed-urls")
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


def strategy_label() -> str:
    return STRATEGY
