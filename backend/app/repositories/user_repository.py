"""User repository for data access operations."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Repository for User model data access operations.

    Provides CRUD operations and custom queries for User model.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: AsyncSession for database operations.
        """
        self.session = session

    async def create(self, user_data: dict[str, Any]) -> User:
        """Create a new user.

        Args:
            user_data: Dictionary containing user attributes.

        Returns:
            User: Created user instance.
        """
        user = User(**user_data)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: str) -> User | None:
        """Get user by ID.

        Args:
            user_id: User's unique identifier.

        Returns:
            User | None: User if found, None otherwise.
        """
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone_number: str) -> User | None:
        """Get user by phone number.

        Args:
            phone_number: User's phone number.

        Returns:
            User | None: User if found, None otherwise.
        """
        result = await self.session.execute(
            select(User).where(User.phone_number == phone_number)
        )
        return result.scalar_one_or_none()

    async def update(self, user_id: str, update_data: dict[str, Any]) -> User | None:
        """Update user by ID.

        Args:
            user_id: User's unique identifier.
            update_data: Dictionary containing attributes to update.

        Returns:
            User | None: Updated user if found, None otherwise.
        """
        user = await self.get_by_id(user_id)
        if user is None:
            return None

        for key, value in update_data.items():
            setattr(user, key, value)

        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete(self, user_id: str) -> bool:
        """Delete user by ID.

        Args:
            user_id: User's unique identifier.

        Returns:
            bool: True if deleted, False if not found.
        """
        user = await self.get_by_id(user_id)
        if user is None:
            return False

        await self.session.delete(user)
        await self.session.commit()
        return True

    async def list_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        """List all users with pagination.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            list[User]: List of users.
        """
        result = await self.session.execute(
            select(User).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
