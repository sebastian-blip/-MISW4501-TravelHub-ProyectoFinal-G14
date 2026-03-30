from __future__ import annotations

import httpx

from service_external.adapters.payment_gateway.config import PaymentGatewaySettings
from service_external.adapters.payment_gateway.schemas import GatewayPaymentIntentDto, GatewayRefundDto
from service_external.contracts.payment import (
    PaymentIntentRequest,
    PaymentIntentResult,
    RefundResult,
    TokenizeCardResult,
)


class GatewayClient:
    def __init__(self, settings: PaymentGatewaySettings | None = None):
        self._s = settings or PaymentGatewaySettings()
        self._client = httpx.Client(
            base_url=self._s.base_url.rstrip("/"),
            timeout=self._s.timeout_seconds,
            verify=self._s.verify_tls,
            headers={"Authorization": f"Bearer {self._s.api_key}"} if self._s.api_key else {},
        )

    def close(self) -> None:
        self._client.close()

    def create_intent(self, body: dict) -> GatewayPaymentIntentDto:
        r = self._client.post("/payment_intents", json=body)
        r.raise_for_status()
        return GatewayPaymentIntentDto.model_validate(r.json())

    def capture_intent(self, intent_id: str, body: dict | None = None) -> GatewayPaymentIntentDto:
        r = self._client.post(f"/payment_intents/{intent_id}/capture", json=body or {})
        r.raise_for_status()
        return GatewayPaymentIntentDto.model_validate(r.json())

    def refund(self, body: dict) -> GatewayRefundDto:
        r = self._client.post("/refunds", json=body)
        r.raise_for_status()
        return GatewayRefundDto.model_validate(r.json())

    def tokenize_transient(self, transient_token: str) -> TokenizeCardResult:
        r = self._client.post("/tokenize", json={"transient_token": transient_token})
        r.raise_for_status()
        data = r.json()
        return TokenizeCardResult(
            payment_method_token=data["payment_method_token"],
            brand=data.get("brand"),
            last4=data.get("last4"),
        )

    def build_intent_body(self, request: PaymentIntentRequest) -> dict:
        return {
            "amount": request.amount_cents,
            "currency": request.currency.lower(),
            "payment_method": request.customer_payment_token,
            "metadata": request.metadata,
        }

    def to_intent_result(self, dto: GatewayPaymentIntentDto) -> PaymentIntentResult:
        return PaymentIntentResult(id=dto.id, status=dto.status, client_secret=dto.client_secret)

    def to_refund_result(self, dto: GatewayRefundDto) -> RefundResult:
        return RefundResult(refund_id=dto.id, status=dto.status)
