"""Notification (Email/SMS) — hexagonal HTTP entry-point (driving adapter)."""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.ports import NotificationPort
from app.adapters import create_adapter
from service_external.contracts.notification import EmailNotificationRequest

app = FastAPI(title="TravelHub Notification", version="0.1.0")
_adapter: NotificationPort | None = None

ADAPTER_STRATEGY = os.getenv("ADAPTER_STRATEGY", "email_sms")


def get_adapter() -> NotificationPort:
    global _adapter
    if _adapter is None:
        _adapter = create_adapter(ADAPTER_STRATEGY)
    return _adapter


@app.get("/health")
def health():
    return {"status": "ok", "service": "notification", "strategy": ADAPTER_STRATEGY}


@app.get("/ready")
def ready():
    return {"ready": True}


class EnqueueEmailBody(BaseModel):
    to: EmailStr
    template_id: str
    locale: str = "es"
    variables: dict[str, str] = Field(default_factory=dict)


@app.post("/v1/notifications/email")
def enqueue_email(body: EnqueueEmailBody):
    try:
        req = EmailNotificationRequest(
            to=body.to,
            template_id=body.template_id,
            locale=body.locale,
            variables=body.variables,
        )
        return get_adapter().enqueue_email(req).model_dump()
    except RuntimeError as e:
        if "circuit_open" in str(e):
            raise HTTPException(status_code=503, detail=str(e)) from e
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail="upstream_notification_error") from e
