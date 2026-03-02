"""Pydantic payloads for PoC-5 events."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UsuarioOlvidadoPayload(BaseModel):
    """Event: user requested right to be forgotten."""
    user_id: str = Field(..., description="ID of the user to anonymize")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="T0 - when the request was accepted (ISO 8601)"
    )
    request_id: Optional[str] = Field(None, description="Optional idempotency/audit key")
