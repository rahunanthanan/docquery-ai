"""Application configuration loaded from environment variables.

All settings are declared here so `.env.example` and this module stay the
single source of truth for configuration. Secrets are never hardcoded.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "DocQuery AI"
    environment: Literal["local", "test", "production"] = "local"

    # Database (used from Task 3 onwards; declared now so compose wiring is testable)
    database_url: str = "postgresql+asyncpg://docquery:docquery@db:5432/docquery"

    # Auth — jwt_secret must be overridden outside local dev (§2: access 15 min,
    # refresh 7 days in an httpOnly cookie)
    jwt_secret: str = "change-me-in-.env"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 7

    # Uploads & quotas (§6)
    upload_dir: str = "/data/uploads"
    max_upload_bytes: int = 20 * 1024 * 1024
    max_documents_per_user: int = 25

    # LLM provider — "fake" runs the whole app with no external API keys
    llm_provider: Literal["fake", "openai", "anthropic"] = "fake"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
