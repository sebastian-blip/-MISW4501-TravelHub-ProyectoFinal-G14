from __future__ import annotations

import uuid
from types import SimpleNamespace

from domains.notification.contracts import (
    EmailNotificationRequest,
    PushNotificationRequest,
    SmsNotificationRequest,
)


class NotificationClient:
    def post_email(self, request: EmailNotificationRequest) -> SimpleNamespace:
        _ = request
        return SimpleNamespace(message_id=f"email-{uuid.uuid4().hex[:8]}", status="queued")

    def post_sms(self, request: SmsNotificationRequest) -> SimpleNamespace:
        _ = request
        return SimpleNamespace(message_id=f"sms-{uuid.uuid4().hex[:8]}", status="queued")

    def post_push(self, request: PushNotificationRequest) -> SimpleNamespace:
        _ = request
        return SimpleNamespace(message_id=f"push-{uuid.uuid4().hex[:8]}", status="queued")
