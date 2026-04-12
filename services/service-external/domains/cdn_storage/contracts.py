from __future__ import annotations

from pydantic import BaseModel, Field


class UploadRequest(BaseModel):
    body_bytes: bytes
    content_type: str | None = None
    filename: str | None = None


class UploadResult(BaseModel):
    asset_id: str
    cdn_url: str


class SignedUrlRequest(BaseModel):
    asset_id: str
    expires_seconds: int = Field(default=3600, ge=60, le=86400)


class SignedUrlResult(BaseModel):
    url: str
    expires_at_iso: str


class SignedUrlDto(BaseModel):
    url: str
    expires_at_iso: str
