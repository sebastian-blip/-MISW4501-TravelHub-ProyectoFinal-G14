from __future__ import annotations

import uuid
from datetime import datetime, timezone

from domains.cdn_storage.ports.storage_port import StoragePort
from domains.cdn_storage.contracts import (
    SignedUrlRequest,
    SignedUrlResult,
    UploadRequest,
    UploadResult,
)


class MockStorageAdapter(StoragePort):
    """In-memory stub for local development and testing."""

    def __init__(self):
        self._assets: dict[str, bytes] = {}

    def upload(self, request: UploadRequest) -> UploadResult:
        asset_id = f"mock-{uuid.uuid4().hex[:8]}"
        self._assets[asset_id] = request.body_bytes
        return UploadResult(asset_id=asset_id, cdn_url=f"http://localhost/mock/{asset_id}")

    def create_signed_read_url(self, request: SignedUrlRequest) -> SignedUrlResult:
        return SignedUrlResult(
            url=f"http://localhost/mock/{request.asset_id}?sig=fake",
            expires_at_iso=datetime.now(timezone.utc).isoformat(),
        )

    def delete_asset(self, asset_id: str) -> None:
        self._assets.pop(asset_id, None)
