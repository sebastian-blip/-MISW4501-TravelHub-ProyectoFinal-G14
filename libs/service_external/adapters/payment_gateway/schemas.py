from __future__ import annotations

from pydantic import BaseModel


class GatewayPaymentIntentDto(BaseModel):
    id: str
    status: str
    client_secret: str | None = None


class GatewayRefundDto(BaseModel):
    id: str
    status: str
