from __future__ import annotations

import httpx

from service_external.adapters.cdn_storage.config import CDNStorageSettings
from service_external.adapters.cdn_storage.schemas import SignedUrlApiResponse, UploadApiResponse
from service_external.contracts.storage import SignedUrlRequest, UploadRequest, UploadResult


class StorageClient:
    def __init__(self, settings: CDNStorageSettings | None = None):
        self._s = settings or CDNStorageSettings()
        self._client = httpx.Client(
            base_url=self._s.base_url.rstrip("/"),
            timeout=self._s.timeout_seconds,
            verify=self._s.verify_tls,
            headers={"Authorization": f"Bearer {self._s.api_key}"} if self._s.api_key else {},
        )

    def close(self) -> None:
        self._client.close()

    def upload(self, request: UploadRequest) -> UploadResult:
        files = {"file": (request.bucket_key, request.body_bytes, request.content_type)}
        data = {"public_read": str(request.public_read).lower()}
        r = self._client.post("/upload", files=files, data=data)
        r.raise_for_status()
        dto = UploadApiResponse.model_validate(r.json())
        return UploadResult(asset_id=dto.asset_id, cdn_url=dto.cdn_url)

    def signed_url(self, request: SignedUrlRequest) -> SignedUrlApiResponse:
        r = self._client.post(
            "/signed-urls",
            json={"asset_id": request.asset_id, "expires_seconds": request.expires_seconds},
        )
        r.raise_for_status()
        return SignedUrlApiResponse.model_validate(r.json())

    def delete(self, asset_id: str) -> None:
        r = self._client.delete(f"/assets/{asset_id}")
        r.raise_for_status()
