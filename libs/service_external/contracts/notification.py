from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class EmailNotificationRequest(BaseModel):
    to: EmailStr
    template_id: str
    locale: str = "es"
    variables: dict[str, str] = Field(default_factory=dict)
    correlation_id: str | None = None


class SmsNotificationRequest(BaseModel):
    to_e164: str
    body: str
    correlation_id: str | None = None


class PushNotificationRequest(BaseModel):
    device_token: str
    title: str
    body: str
    data: dict[str, str] = Field(default_factory=dict)
    correlation_id: str | None = None


class NotificationEnqueueResult(BaseModel):
    queue_message_id: str
    status: str = "queued"
