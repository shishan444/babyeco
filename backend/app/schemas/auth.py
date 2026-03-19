"""Authentication and user schemas for API validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema with common fields."""

    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """Schema for user registration."""

    password: str = Field(..., min_length=8, max_length=100)
    phone: str | None = Field(None, max_length=20)


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user response."""

    id: UUID
    phone: str | None
    avatar_url: str | None
    is_active: bool
    is_verified: bool
    role: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Schema for authentication token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""

    refresh_token: str


class ChildProfileBase(BaseModel):
    """Base child profile schema."""

    name: str = Field(..., min_length=1, max_length=100)
    birth_date: datetime | None = None


class ChildProfileCreate(ChildProfileBase):
    """Schema for creating a child profile."""

    pass


class ChildProfileResponse(ChildProfileBase):
    """Schema for child profile response."""

    id: UUID
    parent_id: UUID
    avatar_url: str | None
    age: int | None
    points_balance: int
    total_points_earned: int
    current_streak: int
    longest_streak: int
    invite_code: str | None
    device_bound: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DeviceBindingRequest(BaseModel):
    """Schema for binding a device to a child profile."""

    invite_code: str = Field(..., min_length=6, max_length=6)


class ChildLoginRequest(BaseModel):
    """Schema for child device login."""

    invite_code: str = Field(..., min_length=6, max_length=6)
