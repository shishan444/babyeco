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
    DeviceBindingRequest,
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

    Creates a child profile and generates an invite code for device binding.
    """
    service = ChildProfileService(db)
    profile = await service.create_profile(current_user.id, profile_data)
    return ChildProfileResponse.model_validate(profile)


@router.get("/", response_model=list[ChildProfileResponse])
async def list_child_profiles(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ChildProfileResponse]:
    """List all child profiles for the current parent."""
    service = ChildProfileService(db)
    profiles = await service.get_profiles_by_parent(current_user.id)
    return [ChildProfileResponse.model_validate(p) for p in profiles]


@router.get("/{profile_id}", response_model=ChildProfileResponse)
async def get_child_profile(
    profile_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChildProfileResponse:
    """Get a specific child profile by ID."""
    service = ChildProfileService(db)
    profile = await service.get_profile(profile_id, current_user.id)
    return ChildProfileResponse.model_validate(profile)


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_child_profile(
    profile_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a child profile."""
    service = ChildProfileService(db)
    await service.delete_profile(profile_id, current_user.id)


@router.post("/{profile_id}/bind-device", response_model=ChildProfileResponse)
async def bind_device(
    profile_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChildProfileResponse:
    """Mark a child profile as device-bound.

    Called after a child successfully logs in with the invite code.
    """
    service = ChildProfileService(db)
    profile = await service.bind_device(profile_id, current_user.id)
    return ChildProfileResponse.model_validate(profile)


@router.post("/bind-with-code", response_model=ChildProfileResponse)
async def bind_with_invite_code(
    request: DeviceBindingRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChildProfileResponse:
    """Bind a device using an invite code (child login).

    This endpoint is used by child devices to authenticate
    using the invite code provided by their parent.
    """
    service = ChildProfileService(db)
    profile = await service.get_profile_by_invite_code(request.invite_code)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid invite code",
        )

    # Bind the device
    bound_profile = await service.bind_device(profile.id, profile.parent_id)
    return ChildProfileResponse.model_validate(bound_profile)


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
