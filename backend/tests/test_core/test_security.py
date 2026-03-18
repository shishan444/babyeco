"""Tests for security module.

RED Phase: These tests define the expected behavior for password hashing and JWT.
"""

import pytest
from datetime import datetime, timedelta, timezone


class TestPasswordHashing:
    """Test suite for password hashing functionality."""

    def test_hash_password_exists(self):
        """hash_password function should exist."""
        from app.core.security import hash_password

        assert callable(hash_password)

    def test_verify_password_exists(self):
        """verify_password function should exist."""
        from app.core.security import verify_password

        assert callable(verify_password)

    def test_hash_password_returns_string(self):
        """hash_password should return a string."""
        from app.core.security import hash_password

        hashed = hash_password("test_password")
        assert isinstance(hashed, str)

    def test_hash_password_is_different_from_plain(self):
        """Hashed password should be different from plain password."""
        from app.core.security import hash_password

        plain = "test_password"
        hashed = hash_password(plain)
        assert hashed != plain

    def test_hash_password_is_bcrypt_format(self):
        """Hashed password should be in bcrypt format."""
        from app.core.security import hash_password

        hashed = hash_password("test_password")
        # bcrypt hashes start with $2b$ or $2a$
        assert hashed.startswith("$2")

    def test_verify_password_correct(self):
        """verify_password should return True for correct password."""
        from app.core.security import hash_password, verify_password

        plain = "test_password"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_password_incorrect(self):
        """verify_password should return False for incorrect password."""
        from app.core.security import hash_password, verify_password

        plain = "test_password"
        hashed = hash_password(plain)
        assert verify_password("wrong_password", hashed) is False

    def test_hash_password_unique_salts(self):
        """Same password should produce different hashes (unique salts)."""
        from app.core.security import hash_password

        plain = "test_password"
        hash1 = hash_password(plain)
        hash2 = hash_password(plain)
        assert hash1 != hash2


class TestJWTToken:
    """Test suite for JWT token functionality."""

    def test_create_access_token_exists(self):
        """create_access_token function should exist."""
        from app.core.security import create_access_token

        assert callable(create_access_token)

    def test_verify_token_exists(self):
        """verify_token function should exist."""
        from app.core.security import verify_token

        assert callable(verify_token)

    def test_create_access_token_returns_string(self):
        """create_access_token should return a string token."""
        from app.core.security import create_access_token

        token = create_access_token(subject="user123")
        assert isinstance(token, str)

    def test_create_access_token_with_expiry(self):
        """create_access_token should accept expiry delta."""
        from app.core.security import create_access_token

        expires = timedelta(hours=1)
        token = create_access_token(
            subject="user123",
            expires_delta=expires,
        )
        assert isinstance(token, str)

    def test_verify_token_returns_payload(self):
        """verify_token should return decoded payload."""
        from app.core.security import create_access_token, verify_token

        token = create_access_token(subject="user123")
        payload = verify_token(token)
        assert payload is not None
        assert isinstance(payload, dict)

    def test_verify_token_contains_sub(self):
        """Decoded token should contain 'sub' (subject) field."""
        from app.core.security import create_access_token, verify_token

        token = create_access_token(subject="user123")
        payload = verify_token(token)
        assert "sub" in payload
        assert payload["sub"] == "user123"

    def test_verify_token_invalid_returns_none(self):
        """verify_token should return None for invalid token."""
        from app.core.security import verify_token

        result = verify_token("invalid_token")
        assert result is None

    def test_verify_token_expired_returns_none(self):
        """verify_token should return None for expired token."""
        from app.core.security import create_access_token, verify_token

        # Create already expired token
        expired_delta = timedelta(seconds=-1)
        token = create_access_token(
            subject="user123",
            expires_delta=expired_delta,
        )
        result = verify_token(token)
        assert result is None


class TestInviteCode:
    """Test suite for invite code generation."""

    def test_generate_invite_code_exists(self):
        """generate_invite_code function should exist."""
        from app.core.security import generate_invite_code

        assert callable(generate_invite_code)

    def test_generate_invite_code_format(self):
        """Invite code should follow format BABY-{8 alphanumeric chars}."""
        from app.core.security import generate_invite_code

        code = generate_invite_code()
        assert code.startswith("BABY-")
        assert len(code) == 13  # "BABY-" (5) + 8 chars
        # Check the 8 chars are alphanumeric
        suffix = code[5:]
        assert suffix.isalnum()

    def test_generate_invite_code_unique(self):
        """Each generated invite code should be unique."""
        from app.core.security import generate_invite_code

        codes = [generate_invite_code() for _ in range(100)]
        assert len(set(codes)) == 100  # All unique
