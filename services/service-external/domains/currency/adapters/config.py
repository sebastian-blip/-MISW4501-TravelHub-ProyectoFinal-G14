from __future__ import annotations

import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class CurrencyExchangeSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TH_FX_")

    cache_ttl_seconds: float = float(os.getenv("TH_FX_CACHE_TTL", "30"))
