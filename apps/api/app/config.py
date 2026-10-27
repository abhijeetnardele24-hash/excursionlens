"""
apps/api/app/config.py — Central Application Settings & Environment Configuration
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# Load .env if present
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
env_path = ROOT_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()


class Settings(BaseSettings):
    app_name: str = "ExcursionLens API"
    app_version: str = "1.0.0"
    app_mode: str = Field(default_factory=lambda: str(os.getenv("APP_MODE") or "live"))

    host: str = Field(default_factory=lambda: str(os.getenv("HOST") or "127.0.0.1"))
    port: int = Field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    log_level: str = Field(default_factory=lambda: str(os.getenv("LOG_LEVEL") or "info"))

    # Nebius Token Factory (Canonical env var: NEBIUS_TOKEN_FACTORY_KEY)
    nebius_key: str = Field(
        default_factory=lambda: str(os.getenv("NEBIUS_TOKEN_FACTORY_KEY") or os.getenv("NEBIUS_API_KEY") or "")
    )
    nebius_base_url: str = Field(
        default_factory=lambda: str(
            os.getenv("NEBIUS_TOKEN_FACTORY_BASE_URL")
            or os.getenv("NEBIUS_BASE_URL")
            or "https://api.tokenfactory.nebius.com/v1/"
        ).rstrip("/") + "/"
    )
    nvidia_fast_model_id: str = Field(
        default_factory=lambda: str(os.getenv("NVIDIA_FAST_MODEL_ID") or "nvidia/nemotron-mini-4b-instruct")
    )
    nvidia_deep_model_id: str = Field(
        default_factory=lambda: str(
            os.getenv("NVIDIA_DEEP_MODEL_ID")
            or os.getenv("DEFAULT_MODEL")
            or "nvidia/llama-3.1-nemotron-70b-instruct"
        )
    )

    # Tavily
    tavily_key: str = Field(default_factory=lambda: str(os.getenv("TAVILY_API_KEY") or ""))

    # CORS and Security
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            o.strip()
            for o in str(
                os.getenv(
                    "CORS_ORIGINS",
                    "http://localhost:8000,http://127.0.0.1:8000,http://localhost:5173,http://127.0.0.1:5173"
                )
            ).split(",")
            if o.strip()
        ]
    )

    # Operational limits & budgets
    max_request_size_bytes: int = Field(default_factory=lambda: int(os.getenv("MAX_REQUEST_SIZE_BYTES", "2097152")))  # 2MB
    rate_limit_per_minute: int = Field(default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "120")))
    investigation_timeout_seconds: int = Field(default_factory=lambda: int(os.getenv("INVESTIGATION_TIMEOUT_SECONDS", "45")))

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }


settings = Settings()
