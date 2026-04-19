from __future__ import annotations

import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CurrencyExchangeSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TH_FX_")

    cache_ttl_seconds: float = Field(default_factory=lambda: float(os.getenv("TH_FX_CACHE_TTL", "30")))
    frankfurter_base_url: str = Field(
        default_factory=lambda: os.getenv("TH_FX_FRANKFURTER_BASE_URL", "https://api.frankfurter.dev").rstrip(
            "/"
        )
    )
    request_timeout_seconds: float = Field(
        default_factory=lambda: float(os.getenv("TH_FX_REQUEST_TIMEOUT", "10"))
    )
