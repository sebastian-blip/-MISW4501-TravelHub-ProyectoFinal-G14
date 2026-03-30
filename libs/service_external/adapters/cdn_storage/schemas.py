from __future__ import annotations

from pydantic import BaseModel


class UploadApiResponse(BaseModel):
    asset_id: str
    cdn_url: str | None = None


class SignedUrlApiResponse(BaseModel):
    url: str
    expires_at_iso: str
