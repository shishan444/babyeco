"""Security utilities for password hashing and JWT token management."""

import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain text password using bcrypt.

    Args:
        password: Plain text password to hash.

    Returns:
        str: Hashed password string.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a hashed password.

    Args:
        plain_password: Plain text password to verify.
        hashed_password: Hashed password to compare against.

    Returns:
        bool: True if password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        subject: Token subject (usually user ID).
        expires_delta: Optional custom expiry time delta.
        additional_claims: Optional additional claims to include.

    Returns:
        str: Encoded JWT token string.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    if additional_claims:
        to_encode.update(additional_claims)

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def verify_token(token: str) -> dict[str, Any] | None:
    """Verify and decode a JWT token.

    Args:
        token: JWT token string to verify.

    Returns:
        dict | None: Decoded payload if valid, None if invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError:
        return None


def generate_invite_code() -> str:
    """Generate a unique invite code.

    Format: BABY-{8 alphanumeric characters}

    Returns:
        str: Generated invite code in format BABY-XXXXXXXX.
    """
    alphabet = string.ascii_uppercase + string.digits
    # Exclude confusing characters: 0, O, 1, I, L
    safe_alphabet = "".join(
        c for c in alphabet if c not in "0O1IL"
    )
    code_suffix = "".join(
        secrets.choice(safe_alphabet)
        for _ in range(settings.INVITE_CODE_LENGTH)
    )
    return f"BABY-{code_suffix}"
