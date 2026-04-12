from __future__ import annotations

from abc import ABC, abstractmethod

from service_external.contracts.notification import (
    EmailNotificationRequest,
    NotificationEnqueueResult,
    PushNotificationRequest,
    SmsNotificationRequest,
)


class NotificationPort(ABC):
    """Contract that any notification adapter must implement."""

    @abstractmethod
    def enqueue_email(self, request: EmailNotificationRequest) -> NotificationEnqueueResult: ...

    @abstractmethod
    def enqueue_sms(self, request: SmsNotificationRequest) -> NotificationEnqueueResult: ...

    @abstractmethod
    def enqueue_push(self, request: PushNotificationRequest) -> NotificationEnqueueResult: ...
