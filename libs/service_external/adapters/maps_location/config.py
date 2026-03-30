from pydantic_settings import BaseSettings, SettingsConfigDict


class MapsSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TH_MAPS_", extra="ignore")

    base_url: str = "https://api.maps-location.example/v1"
    api_key: str = ""
    timeout_seconds: float = 8.0
    verify_tls: bool = True
