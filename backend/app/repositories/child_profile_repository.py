"""Child profile repository for database operations."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.child_profile import ChildProfile


class ChildProfileRepository:
    """Repository for ChildProfile model database operations.

    @MX:ANCHOR
    Primary data access layer for child profiles.
    Handles all CRUD operations for child accounts.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.db = db

    async def create(self, profile: ChildProfile) -> ChildProfile:
        """Create a new child profile."""
        self.db.add(profile)
        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    async def get_by_id(self, profile_id: UUID) -> ChildProfile | None:
        """Get child profile by ID."""
        result = await self.db.execute(
            select(ChildProfile).where(ChildProfile.id == profile_id)
        )
        return result.scalar_one_or_none()

    async def get_by_parent_id(self, parent_id: UUID) -> list[ChildProfile]:
        """Get all child profiles for a parent."""
        result = await self.db.execute(
            select(ChildProfile).where(ChildProfile.parent_id == parent_id)
        )
        return list(result.scalars().all())

    async def get_by_invite_code(self, invite_code: str) -> ChildProfile | None:
        """Get child profile by invite code."""
        result = await self.db.execute(
            select(ChildProfile).where(ChildProfile.invite_code == invite_code)
        )
        return result.scalar_one_or_none()

    async def update(self, profile: ChildProfile) -> ChildProfile:
        """Update an existing child profile."""
        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    async def delete(self, profile: ChildProfile) -> None:
        """Delete a child profile."""
        await self.db.delete(profile)

    async def add_points(self, profile_id: UUID, points: int) -> ChildProfile | None:
        """Add points to a child profile."""
        profile = await self.get_by_id(profile_id)
        if profile:
            profile.points_balance += points
            if points > 0:
                profile.total_points_earned += points
            await self.db.flush()
            await self.db.refresh(profile)
        return profile
