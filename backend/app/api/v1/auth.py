"""Auth API endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_user
from app.core.database import get_db
from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth_service import (
    AuthService,
    AuthenticationError,
    UserAlreadyExistsError,
)

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user."""
    from app.repositories.user_repository import UserRepository

    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo, None)

    try:
        user = await auth_service.register(request)
        token = auth_service.create_access_token(subject=user.id)

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                phone_number=user.phone_number,
                nickname=user.nickname,
                avatar=user.avatar,
                is_active=user.is_active,
                created_at=user.created_at,
            ),
        )
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login with phone and password."""
    from app.repositories.user_repository import UserRepository

    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo, None)

    try:
        result = await auth_service.login(request)
        return TokenResponse(
            access_token=result["access_token"],
            token_type="bearer",
            user=UserResponse(
                id=result["user"]["id"],
                phone_number=result["user"]["phone_number"],
                nickname=result["user"]["nickname"],
                avatar=result["user"]["avatar"],
                is_active=True,
                created_at=datetime.now(),
            ),
        )
    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect phone number or password",
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_user),
):
    """Get current user info."""
    return UserResponse(
        id=current_user.id,
        phone_number=current_user.phone_number,
        nickname=current_user.nickname,
        avatar=current_user.avatar,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token."""
    from app.repositories.user_repository import UserRepository

    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo, None)

    token = credentials.credentials
    payload = auth_service.verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = await user_repo.get_by_id(payload["sub"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    new_token = auth_service.create_access_token(subject=user.id)

    return TokenResponse(
        access_token=new_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            phone_number=user.phone_number,
            nickname=user.nickname,
            avatar=user.avatar,
            is_active=user.is_active,
            created_at=user.created_at,
        ),
    )
