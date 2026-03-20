"""Point system schemas for API validation."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    """Transaction type enumeration."""

    EARN = "earn"
    SPEND = "spend"
    FREEZE = "freeze"
    UNFREEZE = "unfreeze"
    ADJUST = "adjust"
    EXPIRATION = "expiration"


class PointBalanceResponse(BaseModel):
    """Schema for point balance response."""

    balance: int
    frozen: int
    available: int
    total_earned: int
    total_spent: int


class TransactionCreate(BaseModel):
    """Schema for creating a transaction."""

    child_id: UUID
    amount: int = Field(..., gt=1)
    source_type: str
    source_id: UUID | None = None
    description: str | None = None


class TransactionResponse(BaseModel):
    """Schema for transaction response."""

    id: UUID
    child_id: UUID
    type: str
    amount: int
    balance_after: int
    source_type: str | None
    source_id: UUID | None
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    """Schema for paginated transaction list."""

    items: list[TransactionResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class PointFreezeResponse(BaseModel):
    """Schema for point freeze response."""

    id: UUID
    child_id: UUID
    amount: int
    source_type: str | None
    source_id: UUID | None
    status: str
    created_at: datetime
    released_at: datetime | None

    model_config = {"from_attributes": True}


class FreezeRequest(BaseModel):
    """Schema for freezing points."""

    amount: int = Field(..., gt=1)
    source_type: str = "manual"
    source_id: UUID | None = None
    description: str | None = None


class UnfreezeRequest(BaseModel):
    """Schema for unfreezing points."""

    freeze_id: UUID


class AdjustRequest(BaseModel):
    """Schema for manual point adjustment."""

    amount: int
    reason: str = Field(..., min_length=1, max_length=500)


class EarnRequest(BaseModel):
    """Schema for earning points (internal use)."""

    amount: int = Field(..., gt=1)
    source_type: str
    source_id: UUID | None = None
    description: str | None = None


class SpendRequest(BaseModel):
    """Schema for spending points (internal use)."""

    amount: int = Field(..., gt=1)
    source_type: str
    source_id: UUID | None = None
    description: str | None = None
