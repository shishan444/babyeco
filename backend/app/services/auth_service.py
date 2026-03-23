"""Authentication service for user management."""

from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_access_token, decode_token, hash_password, verify_password
from app.models.family import Family
from app.models.token_blacklist import TokenBlacklist
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserCreate


class AuthService:
    """Service handling authentication and user management.

    @MX:NOTE
    Implements authentication logic using phone number as primary identifier.
    Supports parent account registration, login, token management, and logout.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize service with database session."""
        self.db = db
        self.user_repo = UserRepository(db)

    async def register(self, user_data: UserCreate, family_name: str | None = None) -> User:
        """Register a new user account.

        @MX:WARN
        Creates a family automatically on registration (SPEC-BE-AUTH-001 EDR-001).
        Validates phone uniqueness before creating account.
        Passwords are hashed using bcrypt with configurable rounds.
        Phone number must be in E.164 format.
        """
        # Check if phone already exists
        if await self.user_repo.phone_exists(user_data.phone):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered",
            )

        # Create family first (SPEC-BE-AUTH-001 EDR-001)
        family = Family(
            name=family_name or "My Family",
            settings={},
        )
        self.db.add(family)
        await self.db.flush()
        await self.db.refresh(family)

        # Create new user with hashed password
        user = User(
            phone=user_data.phone,
            hashed_password=hash_password(user_data.password),
            name=user_data.name,
            email=user_data.email,  # Optional email
            family_id=family.id,  # Link to family
        )
        return await self.user_repo.create(user)

    async def authenticate(self, phone: str, password: str) -> User:
        """Authenticate user with phone number and password.

        @MX:NOTE
        Returns user if credentials are valid and account is active.
        Updates last_login_at timestamp on successful authentication.
        Raises HTTPException for invalid credentials or inactive accounts.
        """
        user = await self.user_repo.get_by_phone(phone)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid phone number or password",
            )

        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid phone number or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is suspended or deleted",
            )

        # Update last login timestamp
        await self.user_repo.update_last_login(user.id)

        return user

    async def get_current_user(self, user_id: UUID | str) -> User:
        """Get current user by ID.

        @MX:NOTE
        Returns user if found and active.
        Raises HTTPException if user not found or deleted.
        Accepts both UUID and str for compatibility with JWT tokens.
        """
        # Convert string to UUID if needed
        if isinstance(user_id, str):
            user_id = UUID(user_id)

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        return user

    async def update_profile(
        self, user_id: UUID | str, name: str | None = None, avatar_url: str | None = None
    ) -> User:
        """Update user profile information."""
        user = await self.get_current_user(user_id)
        if name:
            user.name = name
        if avatar_url:
            user.avatar_url = avatar_url
        return await self.user_repo.update(user)

    def create_tokens(self, user_id: str) -> dict[str, str | int | UUID]:
        """Create access and refresh tokens for a user.

        @MX:NOTE
        Returns both tokens with expiration time.
        Includes user_id in response for frontend convenience.
        """
        settings = get_settings()
        access_token = create_access_token(
            subject=user_id,
            token_type="access",
        )
        refresh_token = create_access_token(
            subject=user_id,
            token_type="refresh",
        )
        # expires_in in seconds (60 minutes * 60 seconds)
        expires_in = settings.jwt_access_token_expire_minutes * 60
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": expires_in,
            "user_id": UUID(user_id),
        }

    def verify_refresh_token(self, refresh_token: str) -> str:
        """Verify refresh token and return user ID.

        @MX:WARN
        Checks token type and validity.
        Raises HTTPException for invalid or expired tokens.
        """
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        return payload.get("sub")

    async def logout(self, user_id: UUID | str, refresh_token: str) -> None:
        """Logout user by blacklisting their refresh token.

        @MX:NOTE
        Adds refresh token to blacklist to prevent further use.
        Access tokens will expire naturally after their short lifetime.
        """
        # Convert string to UUID if needed
        if isinstance(user_id, str):
            user_id = UUID(user_id)

        payload = decode_token(refresh_token)
        if not payload:
            return  # Invalid token, nothing to blacklist

        token_jti = payload.get("jti") or payload.get("sub")  # Use sub as fallback
        if not token_jti:
            return

        # Calculate expiration time (7 days from now for refresh tokens)
        settings = get_settings()
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.jwt_refresh_token_expire_days
        )

        blacklisted = TokenBlacklist(
            token_jti=token_jti,
            user_id=user_id,
            expires_at=expires_at,
        )
        self.db.add(blacklisted)
        await self.db.commit()

    async def is_token_blacklisted(self, token_jti: str) -> bool:
        """Check if a token has been blacklisted.

        @MX:NOTE
        Returns True if token is in blacklist (logout was called).
        Also cleans up expired blacklist entries.
        """
        # Clean up expired entries first
        await self.db.execute(
            delete(TokenBlacklist).where(
                TokenBlacklist.expires_at < datetime.now(timezone.utc)
            )
        )

        # Check if token is blacklisted
        result = await self.db.execute(
            select(TokenBlacklist).where(TokenBlacklist.token_jti == token_jti)
        )
        return result.scalar_one_or_none() is not None
