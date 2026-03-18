"""Children API endpoints for child profile management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.child_profile import (
    ChildProfileCreateRequest,
    ChildProfileResponse,
    ChildProfileUpdateRequest,
    DeviceBindRequest,
)
from app.services.child_profile_service import ChildProfileService

router = APIRouter(prefix="/children", tags=["children"])


@router.post(
    "/",
    response_model=ChildProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_child_profile(
    request: ChildProfileCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new child profile for the authenticated parent."""
    service = ChildProfileService(db)

    try:
        profile = await service.create_profile(current_user.id, request)
        return ChildProfileResponse.model_validate(profile)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/", response_model=list[ChildProfileResponse])
async def get_children(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all child profiles for the authenticated parent."""
    service = ChildProfileService(db)
    profiles = await service.get_profiles(current_user.id)
    return [ChildProfileResponse.model_validate(p) for p in profiles]


@router.get("/{child_id}", response_model=ChildProfileResponse)
async def get_child_profile(
    child_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific child profile by ID."""
    service = ChildProfileService(db)
    profile = await service.get_profile(child_id, current_user.id)

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child profile not found",
        )

    return ChildProfileResponse.model_validate(profile)


@router.patch("/{child_id}", response_model=ChildProfileResponse)
async def update_child_profile(
    child_id: str,
    request: ChildProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a child profile."""
    service = ChildProfileService(db)
    profile = await service.update_profile(child_id, current_user.id, request)

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child profile not found",
        )

    return ChildProfileResponse.model_validate(profile)


@router.delete("/{child_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_child_profile(
    child_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a child profile."""
    service = ChildProfileService(db)
    deleted = await service.delete_profile(child_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child profile not found",
        )

    return None


@router.post("/bind-device", response_model=ChildProfileResponse)
async def bind_device(
    request: DeviceBindRequest,
    db: AsyncSession = Depends(get_db),
):
    """Bind a device to a child profile using invite code.

    This endpoint does not require authentication - it uses the invite code
    to identify the child profile.
    """
    service = ChildProfileService(db)
    profile = await service.bind_device(request)

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invite code",
        )

    return ChildProfileResponse.model_validate(profile)


@router.post("/{child_id}/regenerate-invite", response_model=ChildProfileResponse)
async def regenerate_invite_code(
    child_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Regenerate invite code for a child profile."""
    service = ChildProfileService(db)
    profile = await service.regenerate_invite_code(child_id, current_user.id)

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child profile not found",
        )

    return ChildProfileResponse.model_validate(profile)
