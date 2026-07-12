from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "VK Kanban API"
    api_prefix: str = "/api"
    database_url: str = Field(
        default_factory=lambda: f"sqlite:///{Path(__file__).resolve().parents[2] / 'kanban.db'}"
    )
    cors_origins: list[str] = ["*"]
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    model_config = SettingsConfigDict(env_file=".env", env_prefix="KANBAN_")


@lru_cache
def get_settings() -> Settings:
    return Settings()
