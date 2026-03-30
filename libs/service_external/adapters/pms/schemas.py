from __future__ import annotations

from pydantic import BaseModel


class WebhookRegisterResponse(BaseModel):
    webhook_id: str
