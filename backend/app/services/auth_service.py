"""Authentication service for user authentication operations."""

from datetime import timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token as _create_access_token,
    hash_password,
    verify_password,
    verify_token as _verify_token,
)
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserRegisterRequest, UserLoginRequest


class AuthenticationError(Exception):
    """Exception raised for authentication errors."""

    pass


class UserAlreadyExistsError(Exception):
    """Exception raised when user already exists."""

    pass


class AuthService:
    """Service for authentication operations.

    Handles user registration, login, and token management.
    """

    def __init__(self, user_repo: UserRepository, session: AsyncSession | None):
        """Initialize auth service.

        Args:
            user_repo: User repository for data access.
            session: Database session (optional, for future use).
        """
        self.user_repo = user_repo
        self.session = session

    async def register(self, request: UserRegisterRequest) -> Any:
        """Register a new user.

        Args:
            request: User registration request data.

        Returns:
            Created user instance.

        Raises:
            UserAlreadyExistsError: If phone number already registered.
        """
        # Check if user already exists
        existing = await self.user_repo.get_by_phone(request.phone_number)
        if existing:
            raise UserAlreadyExistsError(
                f"Phone number {request.phone_number} already registered"
            )

        # Create user
        user_data = {
            "phone_number": request.phone_number,
            "nickname": request.nickname,
            "password_hash": hash_password(request.password),
            "avatar": request.avatar,
        }

        return await self.user_repo.create(user_data)

    async def login(self, request: UserLoginRequest) -> dict[str, Any]:
        """Authenticate user and return token.

        Args:
            request: User login request data.

        Returns:
            Dictionary with access_token, token_type, and user info.

        Raises:
            AuthenticationError: If credentials are invalid.
        """
        # Find user by phone number
        user = await self.user_repo.get_by_phone(request.phone_number)
        if not user:
            raise AuthenticationError("Invalid phone number or password")

        # Verify password
        if not verify_password(request.password, user.password_hash):
            raise AuthenticationError("Invalid phone number or password")

        # Check if user is active
        if not user.is_active:
            raise AuthenticationError("User account is deactivated")

        # Create access token
        access_token = self.create_access_token(subject=user.id)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "phone_number": user.phone_number,
                "nickname": user.nickname,
                "avatar": user.avatar,
            },
        }

    def create_access_token(
        self,
        subject: str | int,
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create a JWT access token.

        Args:
            subject: Token subject (usually user ID).
            expires_delta: Optional custom expiry time.

        Returns:
            JWT token string.
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return _create_access_token(subject=subject, expires_delta=expires_delta)

    def verify_token(self, token: str) -> dict[str, Any] | None:
        """Verify and decode a JWT token.

        Args:
            token: JWT token string.

        Returns:
            Decoded payload if valid, None otherwise.
        """
        return _verify_token(token)
