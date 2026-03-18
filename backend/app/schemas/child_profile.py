"""Child profile schemas for request/response validation."""

from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class ChildProfileCreateRequest(BaseModel):
    """Request schema for creating a child profile."""

    child_name: str = Field(..., min_length=1, max_length=50)
    child_age: int | None = Field(None, ge=6, le=12)
    child_avatar: str | None = Field(None, max_length=500)


class ChildProfileUpdateRequest(BaseModel):
    """Request schema for updating a child profile."""

    child_name: str | None = Field(None, min_length=1, max_length=50)
    child_age: int | None = Field(None, ge=6, le=12)
    child_avatar: str | None = Field(None, max_length=500)


class DeviceBindRequest(BaseModel):
    """Request schema for device binding."""

    invite_code: str = Field(..., min_length=1, max_length=20)
    device_id: str = Field(..., min_length=1, max_length=100)
    device_token: str | None = Field(None, max_length=500)


class ChildProfileResponse(BaseModel):
    """Response schema for child profile."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    child_name: str
    child_age: int
    child_avatar: str | None
    invite_code: str
    invite_code_expires_at: datetime
    points_balance: int
    device_id: str | None
    parent_id: str
    created_at: datetime
