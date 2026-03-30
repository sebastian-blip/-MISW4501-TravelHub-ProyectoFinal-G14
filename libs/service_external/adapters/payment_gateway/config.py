from pydantic_settings import BaseSettings, SettingsConfigDict


class PaymentGatewaySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TH_PAYMENT_", extra="ignore")

    base_url: str = "https://api.payment-gateway.example/v1"
    api_key: str = ""
    timeout_seconds: float = 10.0
    verify_tls: bool = True
