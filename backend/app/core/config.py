"""Application configuration using Pydantic Settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Database Configuration
    DATABASE_URL: str = "sqlite+aiosqlite:///./babyeco.db"

    # JWT Configuration
    SECRET_KEY: str = "babyeco-secret-key-change-in-production-min-32-chars!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours by default

    # Invite Code Configuration
    INVITE_CODE_LENGTH: int = 8
    INVITE_CODE_EXPIRE_DAYS: int = 7

    # Child Profile Limits
    MAX_CHILDREN_PER_PARENT: int = 5


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
