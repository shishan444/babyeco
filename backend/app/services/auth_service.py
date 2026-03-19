"""Authentication service for user management."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, decode_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserCreate


class AuthService:
    """Service handling authentication and user management.

    @MX:NOTE
    Implements authentication logic including registration,
    login, and token management for parent accounts.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize service with database session."""
        self.db = db
        self.user_repo = UserRepository(db)

    async def register(self, user_data: UserCreate) -> User:
        """Register a new user account.

        @MX:WARN
        Validates email uniqueness before creating account.
        Passwords are hashed using bcrypt with configurable rounds.
        """
        # Check if email already exists
        existing_user = await self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Create new user with hashed password
        user = User(
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            name=user_data.name,
            phone=user_data.phone,
        )
        return await self.user_repo.create(user)

    async def authenticate(self, email: str, password: str) -> User:
        """Authenticate user with email and password."""
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )

        return user

    async def get_current_user(self, user_id: UUID) -> User:
        """Get current user by ID."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        return user

    def create_tokens(self, user_id: str) -> dict[str, str]:
        """Create access and refresh tokens for a user."""
        access_token = create_access_token(
            subject=user_id,
            token_type="access",
        )
        refresh_token = create_access_token(
            subject=user_id,
            token_type="refresh",
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    def verify_refresh_token(self, refresh_token: str) -> str:
        """Verify refresh token and return user ID."""
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        return payload.get("sub")
