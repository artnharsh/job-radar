"""
Central configuration.
All settings come from environment variables / .env file.
Never call os.environ directly elsewhere — always import `settings`.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = "development"
    app_name: str = "JobRadar AI"
    app_version: str = "1.0.0"
    secret_key: str = "change-me"

    # Database
    database_url: str
    database_url_sync: str

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # External APIs
    adzuna_app_id: str = ""
    adzuna_app_key: str = ""
    themuse_api_key: str = ""

    # Scheduler
    tier1_poll_interval_minutes: int = 15
    greytier_poll_interval_minutes: int = 30

    # CORS
    allowed_origins: str = "http://localhost:5173"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Module-level singleton — import this everywhere
settings = get_settings()