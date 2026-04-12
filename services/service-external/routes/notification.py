"""HTTP routes for notifications (driving adapter)."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

from domains.notification.adapters import create_adapter
from domains.notification.ports import NotificationPort
from domains.notification.contracts import EmailNotificationRequest

router = APIRouter()
_adapter: NotificationPort | None = None

STRATEGY = os.getenv("NOTIFICATION_ADAPTER_STRATEGY", "email_sms")


def get_adapter() -> NotificationPort:
    global _adapter
    if _adapter is None:
        _adapter = create_adapter(STRATEGY)
    return _adapter


class EnqueueEmailBody(BaseModel):
    to: EmailStr
    template_id: str
    locale: str = "es"
    variables: dict[str, str] = Field(default_factory=dict)


@router.post("/v1/notifications/email")
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


def strategy_label() -> str:
    return STRATEGY
