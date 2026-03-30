from __future__ import annotations

from service_external.adapters.payment_gateway.gateway_client import GatewayClient
from service_external.contracts.payment import TokenizeCardResult


class TokenizationHandler:
    def __init__(self, gateway_client: GatewayClient):
        self._client = gateway_client

    def exchange_transient_token(self, transient_token: str) -> TokenizeCardResult:
        return self._client.tokenize_transient(transient_token)
