"""Task schemas for API validation."""

from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class TaskCategory(str, Enum):
    """Task category enumeration."""

    DAILY = "daily"
    WEEKLY = "weekly"
    ONE_TIME = "one_time"
    FAMILY = "family"


class TaskStatus(str, Enum):
    """Task status enumeration."""

    PENDING = "pending"
    COMPLETED = "completed"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    OVERDUE = "overdue"


class TaskBase(BaseModel):
    """Base task schema with common fields."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    category: TaskCategory = TaskCategory.DAILY
    points: int = Field(default=10, ge=1, le=100)
    due_date: date | None = None
    due_time: str | None = Field(None, pattern=r"^\d{2}:\d{2}$")
    is_recurring: bool = False
    recurrence_pattern: str | None = None


class TaskCreate(TaskBase):
    """Schema for creating a task."""

    child_id: UUID


class TaskUpdate(BaseModel):
    """Schema for updating a task."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    category: TaskCategory | None = None
    points: int | None = Field(None, ge=1, le=100)
    due_date: date | None = None
    due_time: str | None = Field(None, pattern=r"^\d{2}:\d{2}$")
    is_active: bool | None = None


class TaskResponse(TaskBase):
    """Schema for task response."""

    id: UUID
    child_id: UUID
    status: TaskStatus
    streak_bonus: int
    image_url: str | None
    completed_at: datetime | None
    approved_at: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskCompleteRequest(BaseModel):
    """Schema for completing a task."""

    image_proof_url: str | None = None
    notes: str | None = None


class TaskApproveRequest(BaseModel):
    """Schema for approving/rejecting a task."""

    approved: bool
    bonus_points: int = Field(default=0, ge=0, le=50)
    feedback: str | None = None


class TaskCompletionResponse(BaseModel):
    """Schema for task completion response."""

    id: UUID
    task_id: UUID
    child_id: UUID
    completed_date: date
    points_earned: int
    streak_day: int

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    """Schema for task list with filters."""

    tasks: list[TaskResponse]
    total: int
    pending_count: int
    completed_count: int
