"""
apps/api/app/config.py — Central Application Settings
"""

import os

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    app_name: str = "ExcursionLens API"
    app_version: str = "1.0.0"
    app_mode: str = Field(default_factory=lambda: os.getenv("APP_MODE", "live"))

    host: str = Field(default_factory=lambda: os.getenv("HOST", "127.0.0.1"))
    port: int = Field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "info"))

    # Nebius Token Factory
    nebius_key: str = Field(default_factory=lambda: os.getenv("NEBIUS_TOKEN_FACTORY_KEY", ""))
    nebius_base_url: str = Field(
        default_factory=lambda: os.getenv("NEBIUS_TOKEN_FACTORY_BASE_URL", "https://api.tokenfactory.nebius.com/v1/").rstrip("/") + "/"
    )
    nvidia_fast_model_id: str = Field(default_factory=lambda: os.getenv("NVIDIA_FAST_MODEL_ID", "nvidia/nemotron-mini-4b-instruct"))
    nvidia_deep_model_id: str = Field(default_factory=lambda: os.getenv("NVIDIA_DEEP_MODEL_ID", "nvidia/llama-3.1-nemotron-70b-instruct"))

    # Tavily
    tavily_key: str = Field(default_factory=lambda: os.getenv("TAVILY_API_KEY", ""))

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }


settings = Settings()
