from __future__ import annotations

from domains.payment.ports.payment_port import PaymentPort
from domains.payment.adapters.gateway_client import GatewayClient
from domains.payment.adapters.tokenization_handler import TokenizationHandler
from domains.payment.contracts import (
    PaymentIntentRequest,
    PaymentIntentResult,
    RefundRequest,
    RefundResult,
    TokenizeCardResult,
)
from resilience import CircuitBreaker, retry_with_backoff


class PaymentGatewayAdapter(PaymentPort):
    """Driven adapter — calls the payment provider via GatewayClient."""

    def __init__(
        self,
        client: GatewayClient | None = None,
        circuit_breaker: CircuitBreaker | None = None,
    ):
        self._client = client or GatewayClient()
        self._breaker = circuit_breaker or CircuitBreaker()
        self._token_handler = TokenizationHandler(self._client)

    def _guarded(self, fn):
        if not self._breaker.allow():
            raise RuntimeError("payment_gateway_circuit_open")
        try:
            result = retry_with_backoff(fn)
            self._breaker.record_success()
            return result
        except Exception:
            self._breaker.record_failure()
            raise

    def create_payment_intent(self, request: PaymentIntentRequest) -> PaymentIntentResult:
        def _call():
            body = self._client.build_intent_body(request)
            dto = self._client.create_intent(body)
            return self._client.to_intent_result(dto)
        return self._guarded(_call)

    def capture_payment(self, payment_intent_id: str, amount_cents: int | None = None) -> PaymentIntentResult:
        def _call():
            body = {}
            if amount_cents is not None:
                body["amount"] = amount_cents
            dto = self._client.capture_intent(payment_intent_id, body)
            return self._client.to_intent_result(dto)
        return self._guarded(_call)

    def refund(self, request: RefundRequest) -> RefundResult:
        def _call():
            body = {"payment_intent": request.payment_intent_id}
            if request.amount_cents is not None:
                body["amount"] = request.amount_cents
            if request.reason:
                body["reason"] = request.reason
            dto = self._client.refund(body)
            return self._client.to_refund_result(dto)
        return self._guarded(_call)

    def tokenize_payment_method(self, transient_token: str) -> TokenizeCardResult:
        return self._guarded(lambda: self._token_handler.exchange_transient_token(transient_token))
