from pydantic_settings import BaseSettings, SettingsConfigDict


class CurrencyExchangeSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TH_FX_", extra="ignore")

    base_url: str = "https://api.currency-exchange.example/v1"
    api_key: str = ""
    timeout_seconds: float = 5.0
    verify_tls: bool = True
    cache_ttl_seconds: float = 60.0
