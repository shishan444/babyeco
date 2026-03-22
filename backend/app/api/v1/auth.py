"""Authentication API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import CurrentUser, get_current_user
from app.api.middleware.rate_limit import check_rate_limit
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    MessageResponse,
    RefreshTokenRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _rate_limit: None = Depends(check_rate_limit("register")),
) -> UserResponse:
    """Register a new parent account.

    Creates a new user account with phone number and password.
    Phone must be in E.164 format (e.g., +8613812345678).
    Password must meet complexity requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit

    Rate limited: 3 attempts per hour per IP.
    """
    auth_service = AuthService(db)
    user = await auth_service.register(user_data)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
    _rate_limit: None = Depends(check_rate_limit("login")),
) -> TokenResponse:
    """Authenticate user with phone number and password.

    Validates credentials and returns JWT tokens on success.
    Access tokens expire in 1 hour, refresh tokens in 7 days.

    Rate limited: 5 attempts per 15 minutes per IP.
    """
    auth_service = AuthService(db)
    user = await auth_service.authenticate(credentials.phone, credentials.password)
    return auth_service.create_tokens(str(user.id))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_request: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Refresh access token using refresh token.

    Validates refresh token and issues new token pair.
    Old refresh token is not invalidated (token rotation happens on logout).
    """
    auth_service = AuthService(db)
    user_id = auth_service.verify_refresh_token(token_request.refresh_token)

    user = await auth_service.get_current_user(user_id)
    return auth_service.create_tokens(str(user.id))


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser,
) -> UserResponse:
    """Get current authenticated user information.

    Returns the full user profile including phone, name, and status.
    """
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    updates: UserUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """Update current user profile information.

    Allows updating name and avatar_url.
    Phone number cannot be changed after registration.
    """
    auth_service = AuthService(db)
    user = await auth_service.update_profile(
        current_user.id,
        name=updates.name,
        avatar_url=updates.avatar_url,
    )
    return UserResponse.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    refresh_token: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Logout current user and invalidate refresh token.

    Adds the refresh token to the blacklist to prevent further use.
    Access tokens will expire naturally after their short lifetime.

    Request body should contain: {"refresh_token": "..."}
    """
    auth_service = AuthService(db)
    await auth_service.logout(current_user.id, refresh_token)


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _rate_limit: None = Depends(check_rate_limit("forgot_password")),
) -> MessageResponse:
    """Request password reset for a phone number.

    Generates a secure reset token that can be used to reset the password.
    In production, the token would be sent via SMS.

    For testing purposes, the token is returned in a development environment.

    Rate limited: 3 attempts per hour per IP.
    """
    from app.services.password_reset_service import PasswordResetService

    reset_service = PasswordResetService(db)
    token = await reset_service.initiate_reset(request.phone)

    # In production: Send SMS with token
    # For testing: Return token in response (only in dev!)
    return MessageResponse(
        message=f"Password reset token generated (dev mode): {token}"
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    """Reset password using a valid reset token.

    Validates the reset token and updates the user's password.
    The token is single-use and expires after 1 hour.

    Returns success message if password was reset successfully.
    """
    from app.services.password_reset_service import PasswordResetService

    reset_service = PasswordResetService(db)
    await reset_service.reset_password(request)

    return MessageResponse(message="Password has been reset successfully")

