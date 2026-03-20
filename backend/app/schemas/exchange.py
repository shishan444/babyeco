"""Exchange system schemas for API validation."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class RewardType(str, Enum):
    """Reward type enumeration."""

    ONE_TIME = "one_time"
    TIMER = "timer"
    QUANTITY = "quantity"


class RedemptionStatus(str, Enum):
    """Redemption status enumeration."""

    COMPLETED = "completed"
    ACTIVE = "active"
    CANCELLED = "cancelled"


class TimerSessionStatus(str, Enum):
    """Timer session status enumeration."""

    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RewardCreate(BaseModel):
    """Schema for creating a reward."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    image_url: str | None = None
    type: RewardType = Field(default=RewardType.ONE_TIME)
    cost: int = Field(..., ge=1, le=100)
    duration_minutes: int | None = Field(None, ge=1, le=480)
    stock: int | None = Field(None, ge=0)
    enabled: bool = Field(default=True)

    is_active: bool = Field(default=True)

    @field_validator('type')
    @classmethod
    def validate_reward_type(cls, v: RewardType, info) -> RewardType:
        if v == RewardType.TIMER:
            if info.data.get('duration_minutes') is None:
                raise ValueError("duration_minutes required for timer type")

        if v == RewardType.QUANTITY:
            if info.data.get('stock') is None:
                raise ValueError("stock required for quantity type")
        return v


class RewardUpdate(BaseModel):
    """Schema for updating a reward."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    image_url: str | None = None
    type: RewardType | None = None
    cost: int | None = Field(None, ge=1, le=100)
    duration_minutes: int | None = Field(None, ge=1, le=480)
    stock: int | None = Field(None, ge=0)
    enabled: bool | None = None
    is_active: bool | None = None


class RewardResponse(BaseModel):
    """Schema for reward response."""

    id: UUID
    family_id: UUID
    name: str
    description: str | None
    image_url: str | None
    type: RewardType
    cost: int
    duration_minutes: int | None
    stock: int | None
    available_stock: int | None
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RewardListResponse(BaseModel):
    """Schema for reward list response."""

    rewards: list[RewardResponse]
    total: int
    enabled_count: int = 0
    disabled_count: int = 0


class RedemptionResponse(BaseModel):
    """Schema for redemption response."""

    id: UUID
    child_id: UUID
    reward: RewardResponse
    points_spent: int
    type: RewardType
    status: str
    redeemed_at: datetime
    timer_session_id: UUID | None
    completed_at: datetime | None
    notes: str | None
    model_config = {"from_attributes": True}


class RedemptionListResponse(BaseModel):
    """Schema for redemption list response."""

    items: list[RedemptionResponse]
    total: int
    page: int
    page_size: int
    has_more: bool

    model_config = {"from_attributes": True}


class TimerSessionResponse(BaseModel):
    """Schema for timer session response."""

    id: UUID
    child_id: UUID
    reward: RewardResponse
    duration_seconds: int
    remaining_seconds: int
    started_at: datetime
    paused_at: datetime | None
    resumed_at: datetime | None
    completed_at: datetime | None
    status: str
    is_paused: bool
    model_config = {"from_attributes": True}


class PinnedRewardResponse(BaseModel):
    """Schema for pinned reward response."""

    reward_id: UUID
    pinned_at: datetime
    reward: RewardResponse | None
    model_config = {"from_attributes": True}


class RedeemRequest(BaseModel):
    """Schema for redeeming a reward (child device)."""

    reward_id: UUID
    notes: str | None = Field(None, max_length=500)


    model_config = {"from_attributes": True}


class PinRewardRequest(BaseModel):
    """Schema for pinning a reward (child devices)."""

    reward_id: UUID

    model_config = {"from_attributes": True}


# Aliases for backward compatibility (defined after all classes)
RewardCreateRequest = RewardCreate
RewardUpdateRequest = RewardUpdate
