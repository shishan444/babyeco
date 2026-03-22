"""Child device authentication API routes.

@MX:NOTE
Child authentication uses invite codes for device binding.
Each child profile has a unique 6-character invite code.
Devices are bound to prevent unauthorized access.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_child
from app.api.middleware.rate_limit import check_rate_limit
from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token
from app.models.child_profile import ChildProfile, ChildProfileStatus
from app.schemas.auth import (
    ChildLoginRequest,
    ChildLoginResponse,
    ChildProfileResponse,
    DeviceBindingRequest,
    MessageResponse,
)

router = APIRouter()


@router.post("/bind", response_model=ChildProfileResponse)
async def bind_device(
    request: DeviceBindingRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _rate_limit: None = Depends(check_rate_limit("child_bind")),
) -> ChildProfileResponse:
    """Bind a device to a child profile using invite code.

    @MX:NOTE
    Validates the invite code and binds the device to the child profile.
    Each device can only be bound to one profile at a time.
    Each profile can only have one device bound at a time.

    Raises:
        HTTPException: If invite code is invalid or device already bound

    Rate limited: 10 attempts per hour per IP.
    """
    # Find child profile by invite code
    result = await db.execute(
        select(ChildProfile).where(
            ChildProfile.invite_code == request.invite_code.upper(),
            ChildProfile.status == ChildProfileStatus.ACTIVE,
        )
    )
    child = result.scalar_one_or_none()

    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid invite code",
        )

    # Check if device is already bound to another profile
    existing_result = await db.execute(
        select(ChildProfile).where(ChildProfile.device_id == request.device_id)
    )
    existing_child = existing_result.scalar_one_or_none()

    if existing_child:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device is already bound to another profile",
        )

    # Check if profile already has a device bound
    if child.device_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile already has a device bound. "
            "Please unbind the existing device first.",
        )

    # Bind the device
    child.bind_device(request.device_id)
    await db.commit()
    await db.refresh(child)

    return ChildProfileResponse.model_validate(child)


@router.post("/login", response_model=ChildLoginResponse)
async def child_login(
    request: ChildLoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _rate_limit: None = Depends(check_rate_limit("child_login")),
) -> ChildLoginResponse:
    """Authenticate a child device using invite code.

    @MX:NOTE
    Validates invite code and device binding.
    Returns JWT tokens for authenticated child sessions.

    The device_id must match the bound device for the profile.
    If no device is bound yet, this endpoint will bind it automatically.

    Rate limited: 20 attempts per hour per IP.
    """
    # Find child profile by invite code
    result = await db.execute(
        select(ChildProfile).where(
            ChildProfile.invite_code == request.invite_code.upper(),
            ChildProfile.status == ChildProfileStatus.ACTIVE,
        )
    )
    child = result.scalar_one_or_none()

    if not child:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid invite code",
        )

    # Check device binding
    if child.device_id is None:
        # No device bound yet - bind this device
        child.bind_device(request.device_id)
        await db.commit()
    elif child.device_id != request.device_id:
        # Wrong device
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invite code is bound to a different device",
        )

    # Create tokens for child session
    access_token = create_access_token(
        subject=str(child.id),
        additional_claims={"type": "child", "profile_id": str(child.id)},
    )
    refresh_token = create_refresh_token(
        subject=str(child.id),
        additional_claims={"type": "child", "profile_id": str(child.id)},
    )

    await db.refresh(child)

    return ChildLoginResponse(
        profile_id=child.id,
        name=child.name,
        age=child.age,
        avatar_url=child.avatar_url,
        points_balance=child.points_balance,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=3600,  # 1 hour
    )


@router.get("/me", response_model=ChildProfileResponse)
async def get_current_child_profile(
    current_child: Annotated[ChildProfile, Depends(get_current_child)],
) -> ChildProfileResponse:
    """Get current authenticated child profile information.

    Returns the full child profile including points, streaks, and device binding status.
    """
    return ChildProfileResponse.model_validate(current_child)


@router.post("/unbind-device", response_model=MessageResponse)
async def unbind_device(
    current_child: Annotated[ChildProfile, Depends(get_current_child)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    """Unbind the current device from child profile.

    @MX:NOTE
    Allows the child to unbind their device, enabling binding on a new device.
    This is useful when switching devices or troubleshooting.
    """
    current_child.unbind_device()
    await db.commit()

    return MessageResponse(message="Device unbound successfully")
