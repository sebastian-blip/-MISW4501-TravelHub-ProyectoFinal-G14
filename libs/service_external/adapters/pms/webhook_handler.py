from __future__ import annotations

import hashlib
import hmac
from typing import Any

from pydantic import BaseModel, Field


class PMSInventoryWebhookPayload(BaseModel):
    hotel_external_id: str
    event_type: str
    occurred_at_iso: str
    payload: dict[str, Any] = Field(default_factory=dict)


def verify_webhook_signature(body_bytes: bytes, signature_header: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), body_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header.strip())
