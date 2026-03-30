from __future__ import annotations

from app.domains.cdn_storage.ports.storage_port import StoragePort
from service_external.adapters.cdn_storage.storage_client import StorageClient
from service_external.contracts.storage import (
    SignedUrlRequest,
    SignedUrlResult,
    UploadRequest,
    UploadResult,
)
from service_external.resilience import CircuitBreaker, retry_with_backoff


class CDNStorageAdapter(StoragePort):
    """Driven adapter — calls the CDN/Storage provider via StorageClient."""

    def __init__(
        self,
        client: StorageClient | None = None,
        circuit_breaker: CircuitBreaker | None = None,
    ):
        self._client = client or StorageClient()
        self._breaker = circuit_breaker or CircuitBreaker()

    def _run(self, fn):
        if not self._breaker.allow():
            raise RuntimeError("storage_circuit_open")
        try:
            out = retry_with_backoff(fn, max_attempts=2, base_delay=0.5)
            self._breaker.record_success()
            return out
        except Exception:
            self._breaker.record_failure()
            raise

    def upload(self, request: UploadRequest) -> UploadResult:
        return self._run(lambda: self._client.upload(request))

    def create_signed_read_url(self, request: SignedUrlRequest) -> SignedUrlResult:
        def _call():
            dto = self._client.signed_url(request)
            return SignedUrlResult(url=dto.url, expires_at_iso=dto.expires_at_iso)
        return self._run(_call)

    def delete_asset(self, asset_id: str) -> None:
        self._run(lambda: self._client.delete(asset_id))
