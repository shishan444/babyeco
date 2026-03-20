"""Security utilities for password hashing and JWT token handling."""

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=settings.bcrypt_rounds)


def hash_password(password: str) -> str:
    """Hash a plain text password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: str,
    token_type: str = "access",
    expires_delta: timedelta | None = None,
    extra_data: dict[str, Any] | None = None,
) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    elif token_type == "access":
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )
    else:
        expire = datetime.now(UTC) + timedelta(days=settings.jwt_refresh_token_expire_days)

    to_encode: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "exp": expire,
        "iat": datetime.now(UTC),
    }
    if extra_data:
        to_encode.update(extra_data)

    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None


def generate_invite_code() -> str:
    """Generate a random invite code for child device binding."""
    import random
    import string

    chars = string.ascii_uppercase + string.digits
    # Remove confusing characters
    chars = chars.replace("O", "").replace("0", "").replace("I", "").replace("1", "")
    return "".join(random.choices(chars, k=settings.invite_code_length))
