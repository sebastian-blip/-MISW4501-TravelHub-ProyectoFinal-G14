from __future__ import annotations

from service_external.adapters.payment_gateway.gateway_client import GatewayClient
from service_external.adapters.payment_gateway.tokenization_handler import TokenizationHandler
from service_external.contracts.payment import (
    PaymentIntentRequest,
    PaymentIntentResult,
    RefundRequest,
    RefundResult,
    TokenizeCardResult,
)
from service_external.ports.payment_port import PaymentPort
from service_external.resilience import CircuitBreaker, retry_with_backoff


class PaymentGatewayAdapter(PaymentPort):
    def __init__(
        self,
        client: GatewayClient | None = None,
        circuit_breaker: CircuitBreaker | None = None,
    ):
        self._client = client or GatewayClient()
        self._breaker = circuit_breaker or CircuitBreaker()
        self._token_handler = TokenizationHandler(self._client)

    def create_payment_intent(self, request: PaymentIntentRequest) -> PaymentIntentResult:
        if not self._breaker.allow():
            raise RuntimeError("payment_gateway_circuit_open")

        def _call():
            body = self._client.build_intent_body(request)
            dto = self._client.create_intent(body)
            return self._client.to_intent_result(dto)

        try:
            result = retry_with_backoff(_call)
            self._breaker.record_success()
            return result
        except Exception:
            self._breaker.record_failure()
            raise

    def capture_payment(self, payment_intent_id: str, amount_cents: int | None = None) -> PaymentIntentResult:
        if not self._breaker.allow():
            raise RuntimeError("payment_gateway_circuit_open")

        def _call():
            body = {}
            if amount_cents is not None:
                body["amount"] = amount_cents
            dto = self._client.capture_intent(payment_intent_id, body)
            return self._client.to_intent_result(dto)

        try:
            result = retry_with_backoff(_call)
            self._breaker.record_success()
            return result
        except Exception:
            self._breaker.record_failure()
            raise

    def refund(self, request: RefundRequest) -> RefundResult:
        if not self._breaker.allow():
            raise RuntimeError("payment_gateway_circuit_open")

        def _call():
            body = {"payment_intent": request.payment_intent_id}
            if request.amount_cents is not None:
                body["amount"] = request.amount_cents
            if request.reason:
                body["reason"] = request.reason
            dto = self._client.refund(body)
            return self._client.to_refund_result(dto)

        try:
            result = retry_with_backoff(_call)
            self._breaker.record_success()
            return result
        except Exception:
            self._breaker.record_failure()
            raise

    def tokenize_payment_method(self, transient_token: str) -> TokenizeCardResult:
        if not self._breaker.allow():
            raise RuntimeError("payment_gateway_circuit_open")

        def _call():
            return self._token_handler.exchange_transient_token(transient_token)

        try:
            result = retry_with_backoff(_call)
            self._breaker.record_success()
            return result
        except Exception:
            self._breaker.record_failure()
            raise
