"""Child profile service for business logic."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.child_profile import ChildProfile
from app.repositories.child_profile_repository import ChildProfileRepository
from app.schemas.child_profile import (
    ChildProfileCreateRequest,
    ChildProfileUpdateRequest,
    DeviceBindRequest,
)


class ChildProfileService:
    """Service for child profile business logic.

    Handles profile CRUD, device binding, and limit enforcement.
    """

    def __init__(self, session: AsyncSession):
        """Initialize service with database session.

        Args:
            session: AsyncSession for database operations.
        """
        self.session = session
        self.repository = ChildProfileRepository(session)

    async def create_profile(
        self,
        parent_id: str,
        request: ChildProfileCreateRequest,
    ) -> ChildProfile:
        """Create a new child profile for a parent.

        Args:
            parent_id: Parent user's ID.
            request: Profile creation request data.

        Returns:
            ChildProfile: Created child profile.

        Raises:
            ValueError: If profile limit exceeded.
        """
        # Check profile limit
        count = await self.repository.count_by_parent(parent_id)
        if count >= settings.MAX_CHILDREN_PER_PARENT:
            raise ValueError(
                f"Maximum {settings.MAX_CHILDREN_PER_PARENT} child profiles allowed"
            )

        profile_data: dict[str, Any] = {
            "child_name": request.child_name,
            "child_age": request.child_age,
            "parent_id": parent_id,
        }

        if request.child_avatar:
            profile_data["child_avatar"] = request.child_avatar

        return await self.repository.create(profile_data)

    async def get_profiles(self, parent_id: str) -> list[ChildProfile]:
        """Get all child profiles for a parent.

        Args:
            parent_id: Parent user's ID.

        Returns:
            list[ChildProfile]: List of child profiles.
        """
        return await self.repository.get_by_parent(parent_id)

    async def get_profile(self, profile_id: str, parent_id: str) -> ChildProfile | None:
        """Get a specific child profile.

        Args:
            profile_id: Child profile's ID.
            parent_id: Parent user's ID (for ownership verification).

        Returns:
            ChildProfile | None: Profile if found and owned by parent.
        """
        profile = await self.repository.get_by_id(profile_id)
        if profile is None or profile.parent_id != parent_id:
            return None
        return profile

    async def update_profile(
        self,
        profile_id: str,
        parent_id: str,
        request: ChildProfileUpdateRequest,
    ) -> ChildProfile | None:
        """Update a child profile.

        Args:
            profile_id: Child profile's ID.
            parent_id: Parent user's ID (for ownership verification).
            request: Profile update request data.

        Returns:
            ChildProfile | None: Updated profile if found and owned.
        """
        # Verify ownership
        profile = await self.get_profile(profile_id, parent_id)
        if profile is None:
            return None

        update_data: dict[str, Any] = {}
        if request.child_name is not None:
            update_data["child_name"] = request.child_name
        if request.child_age is not None:
            update_data["child_age"] = request.child_age
        if request.child_avatar is not None:
            update_data["child_avatar"] = request.child_avatar

        return await self.repository.update(profile_id, update_data)

    async def delete_profile(self, profile_id: str, parent_id: str) -> bool:
        """Delete a child profile.

        Args:
            profile_id: Child profile's ID.
            parent_id: Parent user's ID (for ownership verification).

        Returns:
            bool: True if deleted, False if not found or not owned.
        """
        # Verify ownership
        profile = await self.get_profile(profile_id, parent_id)
        if profile is None:
            return False

        return await self.repository.delete(profile_id)

    async def bind_device(self, request: DeviceBindRequest) -> ChildProfile | None:
        """Bind a device to a child profile using invite code.

        Args:
            request: Device binding request data.

        Returns:
            ChildProfile | None: Updated profile if invite code is valid.
        """
        profile = await self.repository.get_by_invite_code(request.invite_code)
        if profile is None:
            return None

        # Check if invite code is still valid
        if not profile.is_invite_code_valid():
            return None

        # Bind device
        profile.bind_device(request.device_id, request.device_token)
        await self.session.commit()
        await self.session.refresh(profile)

        return profile

    async def regenerate_invite_code(
        self,
        profile_id: str,
        parent_id: str,
    ) -> ChildProfile | None:
        """Regenerate invite code for a child profile.

        Args:
            profile_id: Child profile's ID.
            parent_id: Parent user's ID (for ownership verification).

        Returns:
            ChildProfile | None: Updated profile with new invite code.
        """
        # Verify ownership
        profile = await self.get_profile(profile_id, parent_id)
        if profile is None:
            return None

        profile.regenerate_invite_code()
        await self.session.commit()
        await self.session.refresh(profile)

        return profile
