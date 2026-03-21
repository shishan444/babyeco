"""Child profile management API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import CurrentUser
from app.core.database import get_db
from app.schemas.auth import (
    ChildProfileCreate,
    ChildProfileResponse,
    ChildProfileUpdate,
    DeviceBindingRequest,
    ChildLoginResponse,
)
from app.services.child_profile_service import ChildProfileService

router = APIRouter()


@router.post("/", response_model=ChildProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_child_profile(
    profile_data: ChildProfileCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChildProfileResponse:
    """Create a new child profile for the current parent.

    Generates a unique 6-character invite code for device binding.
    Maximum 5 child profiles per parent account.
    """
    service = ChildProfileService(db)
    profile = await service.create_profile(current_user.id, profile_data)
    return ChildProfileResponse.model_validate(profile)


@router.get("/", response_model=list[ChildProfileResponse])
async def list_child_profiles(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ChildProfileResponse]:
    """List all active child profiles for the current parent.

    Only returns profiles with status=ACTIVE.
    Archived profiles are not included.
    """
    service = ChildProfileService(db)
    profiles = await service.get_profiles_by_parent(current_user.id)
    return [ChildProfileResponse.model_validate(p) for p in profiles]


@router.get("/{profile_id}", response_model=ChildProfileResponse)
async def get_child_profile(
    profile_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChildProfileResponse:
    """Get a specific child profile by ID.

    Verifies parent ownership before returning the profile.
    """
    service = ChildProfileService(db)
    profile = await service.get_profile(profile_id, current_user.id)
    return ChildProfileResponse.model_validate(profile)


@router.patch("/{profile_id}", response_model=ChildProfileResponse)
async def update_child_profile(
    profile_id: UUID,
    updates: ChildProfileUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChildProfileResponse:
    """Update a child profile's information.

    Allows updating name, avatar_url, and birth_date.
    Invite code and device binding cannot be modified.
    """
    service = ChildProfileService(db)
    profile = await service.update_profile(profile_id, current_user.id, updates)
    return ChildProfileResponse.model_validate(profile)


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_child_profile(
    profile_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Archive (soft delete) a child profile.

    Sets status to ARCHIVED and invalidates the invite code.
    Device binding is also cleared, requiring a new invite to re-bind.
    """
    service = ChildProfileService(db)
    await service.archive_profile(profile_id, current_user.id)


@router.post(
    "/{profile_id}/regenerate-code",
    response_model=ChildProfileResponse,
)
async def regenerate_invite_code(
    profile_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChildProfileResponse:
    """Generate a new invite code for a child profile.

    Invalidates the old invite code immediately.
    Useful if the code was compromised or shared accidentally.
    Device binding is not affected.
    """
    service = ChildProfileService(db)
    profile = await service.regenerate_invite_code(profile_id, current_user.id)
    return ChildProfileResponse.model_validate(profile)


# Child device endpoints (no parent authentication required)
@router.post("/child/bind-with-code", response_model=ChildLoginResponse)
async def bind_device_with_code(
    request: DeviceBindingRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChildLoginResponse:
    """Bind a device using an invite code (child login).

    This endpoint is used by child devices to authenticate
    using the invite code provided by their parent.

    Returns the child profile information along with authentication tokens
    that can be used for subsequent requests.
    """
    service = ChildProfileService(db)
    profile, tokens = await service.bind_device_by_invite_code(
        request.invite_code,
        request.device_id,
    )

    return ChildLoginResponse(
        profile_id=profile.id,
        name=profile.name,
        age=profile.age,
        avatar_url=profile.avatar_url,
        points_balance=profile.points_balance,
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        expires_in=tokens["expires_in"],
    )


@router.get("/child/me", response_model=ChildProfileResponse)
async def get_bound_child_profile(
    device_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChildProfileResponse:
    """Get the child profile for the currently bound device.

    Uses device_id (from device fingerprinting) to identify the child.
    Returns profile information for the child app dashboard.
    """
    service = ChildProfileService(db)
    profile = await service.get_bound_child_by_device(device_id)
    return ChildProfileResponse.model_validate(profile)


@router.post("/child/unbind", status_code=status.HTTP_204_NO_CONTENT)
async def unbind_child_device(
    device_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Unbind the current device from the child profile.

    Clears the device binding, allowing the device to bind to a
    different profile with a new invite code.
    """
    # First get the profile to verify it exists
    service = ChildProfileService(db)
    profile = await service.get_bound_child_by_device(device_id)

    # Then unbind the device
    await service.unbind_device(profile.id)


# Legacy endpoints (for compatibility)
@router.post("/{profile_id}/points", response_model=ChildProfileResponse)
async def add_points(
    profile_id: UUID,
    points: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChildProfileResponse:
    """Add or subtract points from a child profile.

    Positive values add points, negative values subtract points.
    Cannot reduce points below zero.
    """
    service = ChildProfileService(db)
    profile = await service.add_points(profile_id, points)
    return ChildProfileResponse.model_validate(profile)
