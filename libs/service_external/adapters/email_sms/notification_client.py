from __future__ import annotations

import httpx

from service_external.adapters.email_sms.config import EmailSmsSettings
from service_external.adapters.email_sms.schemas import ProviderEnqueueResponse
from service_external.contracts.notification import (
    EmailNotificationRequest,
    PushNotificationRequest,
    SmsNotificationRequest,
)


class NotificationClient:
    def __init__(self, settings: EmailSmsSettings | None = None):
        self._s = settings or EmailSmsSettings()
        self._client = httpx.Client(
            base_url=self._s.base_url.rstrip("/"),
            timeout=self._s.timeout_seconds,
            verify=self._s.verify_tls,
            headers={"Authorization": f"Bearer {self._s.api_key}"} if self._s.api_key else {},
        )

    def close(self) -> None:
        self._client.close()

    def post_email(self, request: EmailNotificationRequest) -> ProviderEnqueueResponse:
        r = self._client.post(
            "/notifications/email",
            json={
                "to": str(request.to),
                "template_id": request.template_id,
                "locale": request.locale,
                "variables": request.variables,
                "correlation_id": request.correlation_id,
            },
        )
        r.raise_for_status()
        return ProviderEnqueueResponse.model_validate(r.json())

    def post_sms(self, request: SmsNotificationRequest) -> ProviderEnqueueResponse:
        r = self._client.post(
            "/notifications/sms",
            json={
                "to": request.to_e164,
                "body": request.body,
                "correlation_id": request.correlation_id,
            },
        )
        r.raise_for_status()
        return ProviderEnqueueResponse.model_validate(r.json())

    def post_push(self, request: PushNotificationRequest) -> ProviderEnqueueResponse:
        r = self._client.post(
            "/notifications/push",
            json={
                "device_token": request.device_token,
                "title": request.title,
                "body": request.body,
                "data": request.data,
                "correlation_id": request.correlation_id,
            },
        )
        r.raise_for_status()
        return ProviderEnqueueResponse.model_validate(r.json())
