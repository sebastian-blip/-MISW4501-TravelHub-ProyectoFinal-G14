from pydantic_settings import BaseSettings, SettingsConfigDict


class PMSSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TH_PMS_", extra="ignore")

    base_url: str = "https://api.pms.example/v1"
    api_key: str = ""
    oauth_token: str = ""
    timeout_seconds: float = 15.0
    verify_tls: bool = True
