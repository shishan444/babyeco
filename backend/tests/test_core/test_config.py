"""Tests for core configuration module.

RED Phase: These tests define the expected behavior for configuration loading.
"""

import pytest


class TestConfig:
    """Test suite for application configuration."""

    def test_settings_loads_from_environment(self):
        """Settings should load from environment variables."""
        from app.core.config import settings

        assert settings is not None
        assert hasattr(settings, "DATABASE_URL")
        assert hasattr(settings, "SECRET_KEY")
        assert hasattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES")

    def test_settings_has_database_url(self):
        """Settings should have DATABASE_URL configured."""
        from app.core.config import settings

        assert settings.DATABASE_URL is not None
        assert isinstance(settings.DATABASE_URL, str)
        assert len(settings.DATABASE_URL) > 0

    def test_settings_has_secret_key(self):
        """Settings should have SECRET_KEY configured."""
        from app.core.config import settings

        assert settings.SECRET_KEY is not None
        assert isinstance(settings.SECRET_KEY, str)
        assert len(settings.SECRET_KEY) >= 32  # Minimum key length for security

    def test_settings_has_token_expiry(self):
        """Settings should have token expiry configuration."""
        from app.core.config import settings

        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES is not None
        assert isinstance(settings.ACCESS_TOKEN_EXPIRE_MINUTES, int)
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0

    def test_settings_has_algorithm(self):
        """Settings should have JWT algorithm configured."""
        from app.core.config import settings

        assert settings.ALGORITHM is not None
        assert settings.ALGORITHM in ["HS256", "HS384", "HS512"]


class TestConfigDefaults:
    """Test default configuration values."""

    def test_default_database_url_format(self):
        """Default DATABASE_URL should be SQLite async format."""
        from app.core.config import settings

        assert "sqlite" in settings.DATABASE_URL.lower()
        assert "aiosqlite" in settings.DATABASE_URL

    def test_default_token_expiry_reasonable(self):
        """Default token expiry should be reasonable (not too long)."""
        from app.core.config import settings

        # Default should be between 15 minutes and 7 days
        assert 15 <= settings.ACCESS_TOKEN_EXPIRE_MINUTES <= 60 * 24 * 7
