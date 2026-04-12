from __future__ import annotations

from app.domains.notification.ports.notification_port import NotificationPort
from service_external.adapters.email_sms.notification_client import NotificationClient
from service_external.contracts.notification import (
    EmailNotificationRequest,
    NotificationEnqueueResult,
    PushNotificationRequest,
    SmsNotificationRequest,
)
from service_external.resilience import CircuitBreaker, retry_with_backoff


class EmailSmsAdapter(NotificationPort):
    """Driven adapter — calls the email/SMS provider via NotificationClient."""

    def __init__(
        self,
        client: NotificationClient | None = None,
        circuit_breaker: CircuitBreaker | None = None,
    ):
        self._client = client or NotificationClient()
        self._breaker = circuit_breaker or CircuitBreaker(failure_threshold=8)

    def _enqueue(self, fn) -> NotificationEnqueueResult:
        if not self._breaker.allow():
            raise RuntimeError("notification_provider_circuit_open")
        try:
            out = retry_with_backoff(fn, max_attempts=4)
            self._breaker.record_success()
            return NotificationEnqueueResult(queue_message_id=out.message_id, status=out.status)
        except Exception:
            self._breaker.record_failure()
            raise

    def enqueue_email(self, request: EmailNotificationRequest) -> NotificationEnqueueResult:
        return self._enqueue(lambda: self._client.post_email(request))

    def enqueue_sms(self, request: SmsNotificationRequest) -> NotificationEnqueueResult:
        return self._enqueue(lambda: self._client.post_sms(request))

    def enqueue_push(self, request: PushNotificationRequest) -> NotificationEnqueueResult:
        return self._enqueue(lambda: self._client.post_push(request))
