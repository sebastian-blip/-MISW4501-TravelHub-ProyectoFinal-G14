from pydantic_settings import BaseSettings, SettingsConfigDict


class EmailSmsSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TH_NOTIFY_", extra="ignore")

    base_url: str = "https://api.email-sms-provider.example/v1"
    api_key: str = ""
    timeout_seconds: float = 8.0
    verify_tls: bool = True
