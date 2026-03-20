"""AI module schemas for chat and question generation."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Message role enumeration."""

    USER = "user"
    ASSISTANT = "assistant"
    PARENT = "parent"


class ChatMessageCreate(BaseModel):
    """Schema for creating a chat message."""

    content: str = Field(..., min_length=1, max_length=2000, description="Message content")
    conversation_id: UUID | None = Field(None, description="Existing conversation ID")


class ChatMessageResponse(BaseModel):
    """Schema for chat message response."""

    id: UUID
    role: MessageRole
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionCreate(BaseModel):
    """Schema for creating a chat session."""

    child_id: UUID = Field(..., description="Child profile ID")


class ChatSessionResponse(BaseModel):
    """Schema for chat session response."""

    id: UUID
    child_id: UUID
    started_at: datetime
    ended_at: datetime | None = None
    message_count: int = 0
    status: str

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    """Schema for conversation with messages."""

    session: ChatSessionResponse
    messages: list[ChatMessageResponse]


class ContentFlagCreate(BaseModel):
    """Schema for creating a content flag."""

    child_id: UUID
    conversation_id: UUID
    message_id: UUID
    flag_type: str = Field(..., description="Type: emotional, inappropriate, safety")
    severity: str = Field(..., description="Level: low, medium, high")
    context: str = Field(..., description="The flagged content")
    reason: str = Field(..., description="AI explanation")


class ContentFlagResponse(BaseModel):
    """Schema for content flag response."""

    id: UUID
    child_id: UUID
    conversation_id: UUID
    message_id: UUID
    flag_type: str
    severity: str
    context: str
    reason: str
    status: str
    reviewed_at: datetime | None = None
    notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ContentFlagUpdate(BaseModel):
    """Schema for updating a content flag."""

    status: str = Field(..., description="Status: pending, reviewed, dismissed")
    notes: str | None = Field(None, description="Review notes")


class GeneratedQuestion(BaseModel):
    """Schema for AI-generated question."""

    question_text: str
    question_type: str = Field(..., description="multiple_choice or short_answer")
    options: list[str] | None = None
    correct_answer: str | None = None
    hint: str | None = None


class QuestionGenerationRequest(BaseModel):
    """Schema for question generation request."""

    content_id: UUID = Field(..., description="Content ID")
    content_text: str = Field(..., description="Content text for question generation")
    age_range: tuple[int, int] = Field(..., description="Target age range")
    count: int = Field(default=3, ge=1, le=10, description="Number of questions")


class QuestionGenerationResponse(BaseModel):
    """Schema for question generation response."""

    content_id: UUID
    questions: list[GeneratedQuestion]


class DailyUsageResponse(BaseModel):
    """Schema for daily usage response."""

    child_id: UUID
    date: str
    question_count: int
    limit: int
    remaining: int


class StreamingChunk(BaseModel):
    """Schema for streaming response chunk."""

    chunk: str | None = None
    done: bool = False
    error: str | None = None
