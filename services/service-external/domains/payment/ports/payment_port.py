from __future__ import annotations

from abc import ABC, abstractmethod

from domains.payment.contracts import (
    PaymentIntentRequest,
    PaymentIntentResult,
    RefundRequest,
    RefundResult,
    TokenizeCardResult,
)


class PaymentPort(ABC):
    """Contract that any payment gateway adapter must implement."""

    @abstractmethod
    def create_payment_intent(self, request: PaymentIntentRequest) -> PaymentIntentResult: ...

    @abstractmethod
    def capture_payment(self, payment_intent_id: str, amount_cents: int | None = None) -> PaymentIntentResult: ...

    @abstractmethod
    def refund(self, request: RefundRequest) -> RefundResult: ...

    @abstractmethod
    def tokenize_payment_method(self, transient_token: str) -> TokenizeCardResult: ...
