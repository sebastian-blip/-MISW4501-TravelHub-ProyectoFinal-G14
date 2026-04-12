from __future__ import annotations

import uuid

from domains.notification.ports.notification_port import NotificationPort
from domains.notification.contracts import (
    EmailNotificationRequest,
    NotificationEnqueueResult,
    PushNotificationRequest,
    SmsNotificationRequest,
)


class MockNotificationAdapter(NotificationPort):
    """In-memory stub — logs notifications without sending anything."""

    def enqueue_email(self, request: EmailNotificationRequest) -> NotificationEnqueueResult:
        return NotificationEnqueueResult(queue_message_id=f"mock-email-{uuid.uuid4().hex[:8]}", status="queued")

    def enqueue_sms(self, request: SmsNotificationRequest) -> NotificationEnqueueResult:
        return NotificationEnqueueResult(queue_message_id=f"mock-sms-{uuid.uuid4().hex[:8]}", status="queued")

    def enqueue_push(self, request: PushNotificationRequest) -> NotificationEnqueueResult:
        return NotificationEnqueueResult(queue_message_id=f"mock-push-{uuid.uuid4().hex[:8]}", status="queued")
