"""Application configuration module."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "BabyEco API"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # API
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default=["http://localhost:3000", "http://localhost:19006"])

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/babyeco"
    )
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")

    # JWT Authentication
    jwt_secret_key: str = Field(default="change-me-in-production-use-secure-random-key")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24  # 24 hours
    jwt_refresh_token_expire_days: int = 30

    # Password Hashing
    bcrypt_rounds: int = 12

    # Security
    invite_code_length: int = 6
    invite_code_expiry_hours: int = 72


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
