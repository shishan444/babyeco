"""User repository for database operations."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserStatus


class UserRepository:
    """Repository for User model database operations.

    @MX:ANCHOR
    Primary data access layer for user accounts.
    Handles all CRUD operations for parent accounts.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.db = db

    async def create(self, user: User) -> User:
        """Create a new user."""
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(
                User.id == user_id,
                User.status != UserStatus.DELETED,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> User | None:
        """Get user by phone number.

        @MX:NOTE
        Phone is the primary identifier for user accounts.
        Returns None if user is deleted.
        """
        result = await self.db.execute(
            select(User).where(
                User.phone == phone,
                User.status != UserStatus.DELETED,
            )
        )
        return result.scalar_one_or_none()

    async def phone_exists(self, phone: str) -> bool:
        """Check if phone number is already registered.

        @MX:NOTE
        Returns True if phone exists (including deleted accounts)
        to prevent re-registration of deleted accounts.
        """
        result = await self.db.execute(
            select(User.id).where(User.phone == phone)
        )
        return result.scalar_one_or_none() is not None

    async def update(self, user: User) -> User:
        """Update an existing user."""
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def soft_delete(self, user: User) -> User:
        """Soft delete a user by setting status to DELETED."""
        user.status = UserStatus.DELETED
        return await self.update(user)

    async def update_last_login(self, user_id: UUID) -> None:
        """Update the last_login_at timestamp for a user."""
        from datetime import datetime, timezone

        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.last_login_at = datetime.now(timezone.utc)
            await self.db.flush()
