"""Child profile service for managing child accounts."""

from datetime import datetime, timezone, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import generate_invite_code
from app.models.child_profile import ChildProfile, ChildProfileStatus
from app.repositories.child_profile_repository import ChildProfileRepository
from app.schemas.auth import ChildProfileCreate, ChildProfileUpdate


class ChildProfileService:
    """Service handling child profile management.

    @MX:NOTE
    Manages child profiles including creation, updates,
    device binding/unbinding, and invite code management.
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
        Generates unique 6-character invite code for device binding.
        Invite code expires in 72 hours (SPEC-BE-AUTH-001).
        Maximum 5 child profiles per parent account.
        Excludes confusing characters (0/O/I/L) from invite codes.
        """
        # Check profile limit
        existing_profiles = await self.profile_repo.get_by_parent_id(parent_id)
        if len(existing_profiles) >= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum number of child profiles reached (5)",
            )

        # Generate unique invite code (retry on collision)
        invite_code = generate_invite_code()
        while await self.profile_repo.get_by_invite_code(invite_code):
            invite_code = generate_invite_code()

        # Calculate invite code expiration (72 hours from now)
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=settings.invite_code_expiry_hours
        )

        # Create profile
        profile = ChildProfile(
            parent_id=parent_id,
            name=profile_data.name,
            birth_date=profile_data.birth_date,
            invite_code=invite_code,
            invite_code_expires_at=expires_at,
            avatar_url=profile_data.avatar_url,
            status=ChildProfileStatus.ACTIVE,
        )
        return await self.profile_repo.create(profile)

    async def get_profiles_by_parent(self, parent_id: UUID) -> list[ChildProfile]:
        """Get all active child profiles for a parent.

        @MX:NOTE
        Only returns profiles with status=ACTIVE.
        Archived profiles are excluded.
        """
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

    async def update_profile(
        self, profile_id: UUID, parent_id: UUID, updates: ChildProfileUpdate
    ) -> ChildProfile:
        """Update a child profile.

        @MX:NOTE
        Allows updating name, avatar_url, and birth_date.
        Invite code and device binding cannot be modified here.
        """
        profile = await self.get_profile(profile_id, parent_id)

        if updates.name is not None:
            profile.name = updates.name
        if updates.avatar_url is not None:
            profile.avatar_url = updates.avatar_url
        if updates.birth_date is not None:
            profile.birth_date = updates.birth_date

        return await self.profile_repo.update(profile)

    async def archive_profile(self, profile_id: UUID, parent_id: UUID) -> ChildProfile:
        """Archive (soft delete) a child profile.

        @MX:NOTE
        Sets status to ARCHIVED and invalidates the invite code.
        Device binding is also cleared.
        """
        profile = await self.get_profile(profile_id, parent_id)

        profile.status = ChildProfileStatus.ARCHIVED
        profile.invite_code = None  # Invalidate invite code
        profile.device_id = None
        profile.device_bound_at = None
        profile.device_bound = False

        return await self.profile_repo.update(profile)

    async def regenerate_invite_code(
        self, profile_id: UUID, parent_id: UUID
    ) -> ChildProfile:
        """Generate a new invite code for a child profile.

        @MX:WARN
        Invalidates the old invite code and resets expiration to 72 hours.
        Useful if the code was compromised or shared accidentally.
        Device binding is not affected.
        """
        profile = await self.get_profile(profile_id, parent_id)

        # Generate new unique invite code
        new_code = generate_invite_code()
        while await self.profile_repo.get_by_invite_code(new_code):
            new_code = generate_invite_code()

        # Reset expiration to 72 hours from now
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=settings.invite_code_expiry_hours
        )

        profile.invite_code = new_code
        profile.invite_code_expires_at = expires_at
        return await self.profile_repo.update(profile)

    async def bind_device_by_invite_code(
        self, invite_code: str, device_id: str
    ) -> tuple[ChildProfile, dict]:
        """Bind a device to a child profile using invite code.

        @MX:WARN
        Returns child profile with authentication tokens.
        Raises exception if code is invalid, expired, already used, or device already bound.

        Returns:
            Tuple of (ChildProfile, token_response)
        """
        profile = await self.profile_repo.get_by_invite_code(invite_code)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid invite code",
            )

        if profile.status != ChildProfileStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Child profile is not active",
            )

        # Check invite code expiration (SPEC-BE-AUTH-001)
        if profile.invite_code_expires_at:
            now = datetime.now(timezone.utc)
            if profile.invite_code_expires_at < now:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invite code has expired",
                )

        if profile.device_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Device already bound to this profile",
            )

        # Check if device is already bound to another profile
        existing = await self.profile_repo.get_by_device_id(device_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Device already bound to another profile",
            )

        # Bind the device
        profile.bind_device(device_id)
        await self.profile_repo.update(profile)

        # Create child tokens (using same JWT structure as parent tokens)
        from app.services.auth_service import AuthService

        auth_service = AuthService(self.db)
        tokens = auth_service.create_tokens(str(profile.id))

        return profile, tokens

    async def unbind_device(self, profile_id: UUID) -> None:
        """Unbind the current device from a child profile.

        @MX:NOTE
        Clears device_id and device_bound_at fields.
        Tokens issued to this device should be invalidated by the client.
        """
        profile = await self.profile_repo.get_by_id(profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child profile not found",
            )

        profile.unbind_device()
        await self.profile_repo.update(profile)

    async def get_bound_child_by_device(self, device_id: str) -> ChildProfile:
        """Get child profile bound to a specific device.

        @MX:NOTE
        Used by child app to retrieve profile after login.
        Returns only active profiles.
        """
        profile = await self.profile_repo.get_by_device_id(device_id)
        if not profile or profile.status != ChildProfileStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active profile found for this device",
            )
        return profile

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
        """Delete a child profile, verifying parent ownership.

        @MX:NOTE
        This is a hard delete. For soft delete, use archive_profile instead.
        """
        profile = await self.get_profile(profile_id, parent_id)
        await self.profile_repo.delete(profile)
