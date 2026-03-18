"""Authentication schemas for request/response validation."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserRegisterRequest(BaseModel):
    """Request schema for user registration."""

    phone_number: str = Field(..., min_length=11, max_length=20)
    nickname: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    avatar: str | None = Field(None, max_length=500)


class UserLoginRequest(BaseModel):
    """Request schema for user login."""

    phone_number: str = Field(..., min_length=11, max_length=20)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Response schema for token."""

    access_token: str
    token_type: str = "bearer"
    user: "UserResponse | None" = None


class UserResponse(BaseModel):
    """Response schema for user info."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    phone_number: str
    nickname: str
    avatar: str | None
    is_active: bool
    created_at: datetime
