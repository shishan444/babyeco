"""Entertainment content schemas for API validation."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class ContentCategory(str, Enum):
    """Content category enumeration."""

    STORY = "story"
    VIDEO = "video"
    AUDIO = "audio"
    ARTICLE = "article"
    GAME = "game"


class ContentType(str, Enum):
    """Content type enumeration."""

    FREE = "free"
    PREMIUM = "premium"


    UNLOCKABLE = "unlockable"


class ContentStatus(str, Enum):
    """Content status enumeration."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ContentBase(BaseModel):
    """Base content schema."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=500)
    content_url: str | None = None
    category: ContentCategory = Field(default=ContentCategory.STORY)
    type: ContentType = Field(default=ContentType.FREE)
    duration_seconds: int | None = None
    age_min: int | None = None
    age_max: int | None = None
    thumbnail_url: str | None = None
    status: ContentStatus = Field(default=ContentStatus.PUBLISHED)
    points_cost: int = Field(default=0, ge=0, le=1000)
    points_reward: int = Field(default=10, ge=1, le=100)
    is_premium: bool = Field(default=False)
    author: str | None = None


    enabled: bool = Field(default=True)


class ContentCreateRequest(ContentBase):
    """Schema for creating content."""

    family_id: UUID
    title: str
    description: str | None = None
    content_url: str | None = None
    category: ContentCategory
 type: ContentType = duration_seconds: int | None = None
    age_min: int | None = None
    age_max: int | None = None
    thumbnail_url: str | None = None
    status: ContentStatus = points_cost: int = Field(default=0, ge=0, le=1000)
    points_reward: int = Field(default=10, ge=1, le=100)
    is_premium: bool = Field(default=False)
    author: str | None = None
    enabled: bool = Field(default=True)


class ContentUpdateRequest(BaseModel):
    """Schema for updating content."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=500)
    content_url: str | None = None
    category: ContentCategory | None
 None
    type: ContentType | None = None
    duration_seconds: int | None = None
    age_min: int | None = None
    age_max: int | None = None
    thumbnail_url: str | None = None
    status: ContentStatus | None = None
    points_cost: int | None = Field(None, ge=0, le=100)
    points_reward: int | None = Field(None, ge=1, le=100)
    is_premium: bool | None = None
    author: str | None = None
    enabled: bool | None = None


class ContentResponse(ContentBase):
    """Schema for content response."""

    id: UUID
    family_id: UUID
    title: str
    description: str | None
    content_url: str | None
    category: ContentCategory
    type: ContentType
    duration_seconds: int | None
    age_min: int | None
    age_max: int | None
    thumbnail_url: str | None
    status: ContentStatus
    points_cost: int
    points_reward: int
    is_premium: bool
    author: str | None
    created_by: UUID
    created_at: datetime
    enabled: bool

    model_config = {"from_attributes": True}


class ContentListResponse(BaseModel):
    """Schema for content list response."""

    contents: list[ContentResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class ContentProgressResponse(BaseModel):
    """Schema for content progress response."""

    id: UUID
    content_id: UUID
    progress_seconds: int
    completed: bool
    points_earned: int
    last_position: int | None
    started_at: datetime
    completed_at: datetime | None
    last_updated_at: datetime

    model_config = {"from_attributes": True}


class ContentUnlockResponse(BaseModel):
    """Schema for content unlock response."""

    id: UUID
    content_id: UUID
    points_spent: int
    unlocked_at: datetime
    expires_at: datetime | None

    model_config = {"from_attributes": True}


class UpdateProgressRequest(BaseModel):
    """Schema for updating progress."""

    progress_seconds: int
    last_position: int | None


    completed: bool = False


class CompleteContentRequest(BaseModel):
    """Schema for marking content complete."""

    points_bonus: int = Field(default=0, ge=0, le=50)


    answers_correct: int | Field(default=0, ge=0, le=10)
    notes: str | None = None


class QuestionSessionRequest(BaseModel):
    """Schema for AI question session."""

    content_id: UUID
    child_age: int
    model_config = {"from_attributes": True}


class QuestionSessionResponse(BaseModel):
    """Schema for question session response."""

    id: UUID
    content_id: UUID
    questions: list[str]
    total_questions: int
    correct_answers: int
    points_earned: int
    completed_at: datetime

    model_config = {"from_attributes": True}
