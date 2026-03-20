"""Authentication dependencies for API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.child_profile import ChildProfile
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.child_profile_service import ChildProfileService

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Get the current authenticated user from JWT token.

    @MX:ANCHOR
    Dependency used across all protected API endpoints.
    Validates JWT token and returns the authenticated user.
    """
    token = credentials.credentials
    payload = decode_token(token)

    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(UUID(user_id))

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Verify the current user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_child(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChildProfile:
    """Get the current authenticated child profile from JWT token.

    @MX:NOTE
    Dependency used for child device API endpoints.
    Validates JWT token and returns the authenticated child profile.
    """
    token = credentials.credentials
    payload = decode_token(token)

    if not payload or payload.get("type") != "child_access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired child token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    child_id = payload.get("sub")
    if not child_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    child_service = ChildProfileService(db)
    child = await child_service.get_by_id(UUID(child_id))

    if not child:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Child profile not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return child


# Type alias for dependency injection
CurrentUser = Annotated[User, Depends(get_current_active_user)]
CurrentChild = Annotated[ChildProfile, Depends(get_current_child)]
