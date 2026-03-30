from __future__ import annotations

from pydantic import BaseModel


class ProviderEnqueueResponse(BaseModel):
    message_id: str
    status: str = "queued"
