from __future__ import annotations

import uuid

from domains.payment.contracts import PaymentIntentRequest, PaymentIntentResult, RefundResult


class GatewayClient:
    """HTTP-less stub; returns provider-shaped dicts for the payment adapter."""

    def build_intent_body(self, request: PaymentIntentRequest) -> dict:
        return {
            "amount": request.amount_cents,
            "currency": request.currency.lower(),
            "payment_method": request.customer_payment_token,
        }

    def create_intent(self, body: dict) -> dict:
        return {
            "id": f"pi_mock_{uuid.uuid4().hex[:10]}",
            "status": "requires_capture",
            "client_secret": f"cs_mock_{uuid.uuid4().hex[:12]}",
        }

    def to_intent_result(self, dto: dict) -> PaymentIntentResult:
        return PaymentIntentResult(
            id=dto["id"],
            status=dto["status"],
            client_secret=dto.get("client_secret"),
        )

    def capture_intent(self, payment_intent_id: str, body: dict) -> dict:
        return {"id": payment_intent_id, "status": "succeeded"}

    def refund(self, body: dict) -> dict:
        return {"id": f"re_{uuid.uuid4().hex[:10]}", "status": "succeeded"}

    def to_refund_result(self, dto: dict) -> RefundResult:
        return RefundResult(refund_id=dto["id"], status=dto["status"])
