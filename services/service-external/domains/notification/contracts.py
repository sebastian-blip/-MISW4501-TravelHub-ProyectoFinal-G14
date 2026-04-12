from __future__ import annotations

from pydantic import BaseModel, Field


class EmailNotificationRequest(BaseModel):
    to: str
    template_id: str
    locale: str = "es"
    variables: dict[str, str] = Field(default_factory=dict)


class SmsNotificationRequest(BaseModel):
    phone: str
    template_id: str
    variables: dict[str, str] = Field(default_factory=dict)


class PushNotificationRequest(BaseModel):
    user_id: str
    title: str
    body: str


class NotificationEnqueueResult(BaseModel):
    queue_message_id: str
    status: str
