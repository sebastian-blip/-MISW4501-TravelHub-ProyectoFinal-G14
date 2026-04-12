from __future__ import annotations

from abc import ABC, abstractmethod

from domains.cdn_storage.contracts import (
    SignedUrlRequest,
    SignedUrlResult,
    UploadRequest,
    UploadResult,
)


class StoragePort(ABC):
    """Contract that any storage adapter must implement."""

    @abstractmethod
    def upload(self, request: UploadRequest) -> UploadResult: ...

    @abstractmethod
    def create_signed_read_url(self, request: SignedUrlRequest) -> SignedUrlResult: ...

    @abstractmethod
    def delete_asset(self, asset_id: str) -> None: ...
