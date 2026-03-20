"""Authentication API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import (
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """Register a new parent account.

    Creates a new user account with the provided credentials.
    Returns the created user information.
    """
    auth_service = AuthService(db)
    user = await auth_service.register(user_data)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Authenticate user and return tokens.

    Validates email and password, returns JWT tokens on success.
    """
    auth_service = AuthService(db)
    user = await auth_service.authenticate(credentials.email, credentials.password)
    return auth_service.create_tokens(str(user.id))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_request: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Refresh access token using refresh token.

    Validates refresh token and issues new token pair.
    """
    auth_service = AuthService(db)
    user_id = auth_service.verify_refresh_token(token_request.refresh_token)

    user_repo = await auth_service.user_repo.get_by_id(user_id)
    if not user_repo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return auth_service.create_tokens(str(user_repo.id))


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser,
) -> UserResponse:
    """Get current authenticated user information."""
    return UserResponse.model_validate(current_user)


@router.post("/logout")
async def logout(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Logout current user.

    Note: In a production system, this would invalidate the token
    by adding it to a blacklist in Redis.
    """
    return {"message": "Successfully logged out"}
