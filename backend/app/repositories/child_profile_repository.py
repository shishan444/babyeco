"""Child profile repository for data access operations."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.child_profile import ChildProfile


class ChildProfileRepository:
    """Repository for ChildProfile model data access operations.

    Provides CRUD operations and custom queries for ChildProfile model.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: AsyncSession for database operations.
        """
        self.session = session

    async def create(self, profile_data: dict[str, Any]) -> ChildProfile:
        """Create a new child profile.

        Args:
            profile_data: Dictionary containing child profile attributes.

        Returns:
            ChildProfile: Created child profile instance.
        """
        profile = ChildProfile(**profile_data)
        self.session.add(profile)
        await self.session.commit()
        await self.session.refresh(profile)
        return profile

    async def get_by_id(self, profile_id: str) -> ChildProfile | None:
        """Get child profile by ID.

        Args:
            profile_id: Child profile's unique identifier.

        Returns:
            ChildProfile | None: Profile if found, None otherwise.
        """
        result = await self.session.execute(
            select(ChildProfile).where(ChildProfile.id == profile_id)
        )
        return result.scalar_one_or_none()

    async def get_by_parent(
        self, parent_id: str, skip: int = 0, limit: int = 100
    ) -> list[ChildProfile]:
        """Get all child profiles for a parent.

        Args:
            parent_id: Parent user's unique identifier.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            list[ChildProfile]: List of child profiles for the parent.
        """
        result = await self.session.execute(
            select(ChildProfile)
            .where(ChildProfile.parent_id == parent_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_invite_code(self, invite_code: str) -> ChildProfile | None:
        """Get child profile by invite code.

        Args:
            invite_code: Unique invite code.

        Returns:
            ChildProfile | None: Profile if found, None otherwise.
        """
        result = await self.session.execute(
            select(ChildProfile).where(ChildProfile.invite_code == invite_code)
        )
        return result.scalar_one_or_none()

    async def count_by_parent(self, parent_id: str) -> int:
        """Count child profiles for a parent.

        Args:
            parent_id: Parent user's unique identifier.

        Returns:
            int: Number of child profiles.
        """
        result = await self.session.execute(
            select(func.count(ChildProfile.id)).where(
                ChildProfile.parent_id == parent_id
            )
        )
        return result.scalar() or 0

    async def update(
        self, profile_id: str, update_data: dict[str, Any]
    ) -> ChildProfile | None:
        """Update child profile by ID.

        Args:
            profile_id: Child profile's unique identifier.
            update_data: Dictionary containing attributes to update.

        Returns:
            ChildProfile | None: Updated profile if found, None otherwise.
        """
        profile = await self.get_by_id(profile_id)
        if profile is None:
            return None

        for key, value in update_data.items():
            setattr(profile, key, value)

        await self.session.commit()
        await self.session.refresh(profile)
        return profile

    async def delete(self, profile_id: str) -> bool:
        """Delete child profile by ID.

        Args:
            profile_id: Child profile's unique identifier.

        Returns:
            bool: True if deleted, False if not found.
        """
        profile = await self.get_by_id(profile_id)
        if profile is None:
            return False

        await self.session.delete(profile)
        await self.session.commit()
        return True
