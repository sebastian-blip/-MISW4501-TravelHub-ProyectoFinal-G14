from __future__ import annotations

import uuid

from app.ports.payment_port import PaymentPort
from service_external.contracts.payment import (
    PaymentIntentRequest,
    PaymentIntentResult,
    RefundRequest,
    RefundResult,
    TokenizeCardResult,
)


class MockPaymentAdapter(PaymentPort):
    """In-memory stub for local development and testing."""

    def create_payment_intent(self, request: PaymentIntentRequest) -> PaymentIntentResult:
        return PaymentIntentResult(
            id=f"pi_mock_{uuid.uuid4().hex[:8]}",
            status="requires_capture",
            client_secret=f"cs_mock_{uuid.uuid4().hex[:12]}",
        )

    def capture_payment(self, payment_intent_id: str, amount_cents: int | None = None) -> PaymentIntentResult:
        return PaymentIntentResult(id=payment_intent_id, status="succeeded")

    def refund(self, request: RefundRequest) -> RefundResult:
        return RefundResult(refund_id=f"re_mock_{uuid.uuid4().hex[:8]}", status="succeeded")

    def tokenize_payment_method(self, transient_token: str) -> TokenizeCardResult:
        return TokenizeCardResult(payment_method_token=f"pm_mock_{uuid.uuid4().hex[:8]}", brand="visa", last4="4242")
