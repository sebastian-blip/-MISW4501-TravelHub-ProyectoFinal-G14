from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from domains.cdn_storage.contracts import SignedUrlRequest, UploadRequest


class StorageClient:
    def upload(self, request: UploadRequest) -> SimpleNamespace:
        asset_id = f"stub-{uuid.uuid4().hex[:8]}"
        return SimpleNamespace(asset_id=asset_id, cdn_url=f"https://cdn.example/{asset_id}")

    def signed_url(self, request: SignedUrlRequest) -> SimpleNamespace:
        return SimpleNamespace(
            url=f"https://cdn.example/{request.asset_id}?sig=stub",
            expires_at_iso=datetime.now(timezone.utc).isoformat(),
        )

    def delete(self, asset_id: str) -> None:
        _ = asset_id
