from __future__ import annotations

from pydantic import BaseModel, Field


class UploadRequest(BaseModel):
    bucket_key: str
    content_type: str
    body_bytes: bytes
    public_read: bool = False


class UploadResult(BaseModel):
    asset_id: str
    cdn_url: str | None = None


class SignedUrlRequest(BaseModel):
    asset_id: str
    expires_seconds: int = 3600


class SignedUrlResult(BaseModel):
    url: str
    expires_at_iso: str
