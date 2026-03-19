"""Child profile service for managing child accounts."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_invite_code
from app.models.child_profile import ChildProfile
from app.repositories.child_profile_repository import ChildProfileRepository
from app.schemas.auth import ChildProfileCreate


class ChildProfileService:
    """Service handling child profile management.

    @MX:NOTE
    Manages child profiles including creation,
    device binding, and point management.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize service with database session."""
        self.db = db
        self.profile_repo = ChildProfileRepository(db)

    async def create_profile(
        self, parent_id: UUID, profile_data: ChildProfileCreate
    ) -> ChildProfile:
        """Create a new child profile for a parent.

        @MX:WARN
        Generates unique invite code for device binding.
        Maximum 5 child profiles per parent.
        """
        # Check profile limit
        existing_profiles = await self.profile_repo.get_by_parent_id(parent_id)
        if len(existing_profiles) >= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum number of child profiles reached (5)",
            )

        # Generate unique invite code
        invite_code = generate_invite_code()
        while await self.profile_repo.get_by_invite_code(invite_code):
            invite_code = generate_invite_code()

        # Create profile with birth_date handling
        birth_date = profile_data.birth_date.date() if profile_data.birth_date else None

        profile = ChildProfile(
            parent_id=parent_id,
            name=profile_data.name,
            birth_date=birth_date,
            invite_code=invite_code,
        )
        return await self.profile_repo.create(profile)

    async def get_profiles_by_parent(self, parent_id: UUID) -> list[ChildProfile]:
        """Get all child profiles for a parent."""
        return await self.profile_repo.get_by_parent_id(parent_id)

    async def get_profile(self, profile_id: UUID, parent_id: UUID) -> ChildProfile:
        """Get a child profile by ID, verifying parent ownership."""
        profile = await self.profile_repo.get_by_id(profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child profile not found",
            )
        if profile.parent_id != parent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
        return profile

    async def bind_device(self, invite_code: str) -> ChildProfile:
        """Bind a device to a child profile using invite code."""
        profile = await self.profile_repo.get_by_invite_code(invite_code)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid invite code",
            )
        if profile.device_bound:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This code has already been used",
            )

        profile.device_bound = True
        return await self.profile_repo.update(profile)

    async def add_points(self, profile_id: UUID, points: int) -> ChildProfile:
        """Add or subtract points from a child profile."""
        profile = await self.profile_repo.get_by_id(profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child profile not found",
            )

        # Prevent negative balance
        if profile.points_balance + points < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient points",
            )

        return await self.profile_repo.add_points(profile_id, points)

    async def delete_profile(self, profile_id: UUID, parent_id: UUID) -> None:
        """Delete a child profile, verifying parent ownership."""
        profile = await self.get_profile(profile_id, parent_id)
        await self.profile_repo.delete(profile)
