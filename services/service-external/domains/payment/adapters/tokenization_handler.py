from __future__ import annotations

import uuid

from domains.payment.adapters.gateway_client import GatewayClient
from domains.payment.contracts import TokenizeCardResult


class TokenizationHandler:
    def __init__(self, client: GatewayClient) -> None:
        self._client = client

    def exchange_transient_token(self, transient_token: str) -> TokenizeCardResult:
        _ = transient_token
        return TokenizeCardResult(
            payment_method_token=f"pm_mock_{uuid.uuid4().hex[:8]}",
            brand="visa",
            last4="4242",
        )
