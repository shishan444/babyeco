"""Password reset service for managing forgot-password flow.

@MX:NOTE
Uses in-memory token storage for simplicity. In production, use Redis
or a database table with proper expiration handling.
"""

from datetime import datetime, timedelta, timezone
from secrets import token_hex
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import ResetPasswordRequest


class PasswordResetService:
    """Service for managing password reset tokens and operations.

    @MX:ANCHOR
    Handles the forgot-password flow including token generation,
    validation, and password updates.
    """

    # In-memory token storage (use Redis in production)
    _reset_tokens: dict[str, dict] = {}

    # Token expiration time (1 hour)
    TOKEN_EXPIRATION_HOURS = 1

    def __init__(self, db: AsyncSession) -> None:
        """Initialize password reset service.

        Args:
            db: Database session for user operations
        """
        self.db = db

    async def initiate_reset(self, phone: str) -> str:
        """Initiate password reset for a phone number.

        @MX:NOTE
        Generates a secure reset token and stores it with expiration.
        In production, send this token via SMS to the user's phone.

        Args:
            phone: User's phone number in E.164 format

        Returns:
            The reset token (in production, this would be sent via SMS)

        Raises:
            HTTPException: If phone number not found
        """
        # Find user by phone
        result = await self.db.execute(
            select(User).where(User.phone == phone, User.status == UserStatus.ACTIVE)
        )
        user = result.scalar_one_or_none()

        if not user:
            # Don't reveal if phone exists or not for security
            # But still raise an error to prevent timing attacks
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="If an account exists with this phone number, "
                "a reset token will be generated",
            )

        # Generate secure token
        reset_token = token_hex(32)

        # Store token with expiration
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=self.TOKEN_EXPIRATION_HOURS
        )

        self._reset_tokens[reset_token] = {
            "user_id": str(user.id),
            "expires_at": expires_at.isoformat(),
        }

        # In production: Send SMS with reset token
        # For now, return token for testing
        return reset_token

    async def reset_password(self, request: ResetPasswordRequest) -> None:
        """Reset user password using valid reset token.

        @MX:NOTE
        Validates token, updates password, and invalidates token.
        Token is single-use only.

        Args:
            request: Reset password request with token and new password

        Raises:
            HTTPException: If token is invalid, expired, or user not found
        """
        # Check if token exists
        token_data = self._reset_tokens.get(request.token)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        # Check expiration
        expires_at = datetime.fromisoformat(token_data["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            # Remove expired token
            del self._reset_tokens[request.token]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired",
            )

        # Get user
        user_id = UUID(token_data["user_id"])
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Import auth service for password hashing
        from app.services.auth_service import AuthService

        auth_service = AuthService(self.db)

        # Update password
        user.hashed_password = auth_service._hash_password(request.new_password)
        await self.db.commit()

        # Invalidate token (single-use)
        del self._reset_tokens[request.token]

    @classmethod
    def cleanup_expired_tokens(cls) -> int:
        """Remove expired tokens from storage.

        @MX:NOTE
        This should be called periodically (e.g., via Celery beat).
        Returns the number of tokens removed.

        Returns:
            Number of expired tokens removed
        """
        now = datetime.now(timezone.utc)
        expired_tokens = []

        for token, data in cls._reset_tokens.items():
            expires_at = datetime.fromisoformat(data["expires_at"])
            if now > expires_at:
                expired_tokens.append(token)

        for token in expired_tokens:
            del cls._reset_tokens[token]

        return len(expired_tokens)


# Type alias for dependency injection
PasswordResetServiceDep = Annotated[
    PasswordResetService, Depends(lambda db=Depends(get_db): PasswordResetService(db))
]
