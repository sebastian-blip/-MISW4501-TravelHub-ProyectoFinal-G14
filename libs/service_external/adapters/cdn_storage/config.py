from pydantic_settings import BaseSettings, SettingsConfigDict


class CDNStorageSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TH_STORAGE_", extra="ignore")

    base_url: str = "https://api.cdn-storage.example/v1"
    api_key: str = ""
    timeout_seconds: float = 60.0
    verify_tls: bool = True
