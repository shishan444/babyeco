"""AI module models for chat and question generation."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.child_profile import ChildProfile
    from app.models.content import Content


class MessageRole(str, Enum):
    """Message role enumeration."""

    USER = "user"
    ASSISTANT = "assistant"
    PARENT = "parent"


class ChatSession(Base, TimestampMixin):
    """Chat session model for tracking conversations.

    @MX:ANCHOR
    Core session entity for AI chat.
    Tracks conversation history and context.
    """

    __tablename__ = "chat_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    child_id: Mapped[UUID] = mapped_column(
        ForeignKey("child_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    context: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Store conversation context as JSON
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False,
        index=True,
    )

    # Relationships
    child: Mapped["ChildProfile"] = relationship("ChildProfile", backref="chat_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="session"
    )

    def __repr__(self) -> str:
        return f"<ChatSession(id={self.id}, status={self.status})>"


class ChatMessage(Base, TimestampMixin):
    """Chat message model for individual messages.

    @MX:NOTE
    Stores each message in a chat session
    Supports user and assistant roles
    """

    __tablename__ = "chat_messages"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[MessageRole] = mapped_column(
        String(20),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    finish_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    session: Mapped["ChatSession"] = relationship(
        "ChatSession",
        back_populates="messages",
    )

    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, role={self.role})>"


class QuestionSet(Base, TimestampMixin):
    """Question set model for AI-generated questions.

    @MX:NOTE
    Groups questions for content completion
    Links to entertainment content
    """

    __tablename__ = "question_sets"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    content_id: Mapped[UUID] = mapped_column(
        ForeignKey("contents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    questions: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array of questions
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
    )

    # Relationships
    content: Mapped["Content"] = relationship("Content", backref="question_sets")

    def __repr__(self) -> str:
        return f"<QuestionSet(id={self.id}, content_id={self.content_id}, status={self.status})>"


class SafetyFilterResult(Base, TimestampMixin):
    """Safety filter result for content moderation.

    @MX:ANCHOR
    Records AI response safety checks
    Used for audit and parent notification
    """

    __tablename__ = "safety_filter_results"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    message_id: Mapped[UUID] = mapped_column(
        ForeignKey("chat_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filter_type: Mapped[str] = mapped_column(String(50), nullable=False)
    flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    action_taken: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    message: Mapped["ChatMessage"] = relationship("ChatMessage", backref="filter_results")

    def __repr__(self) -> str:
        return f"<SafetyFilterResult(id={self.id}, filter_type={self.filter_type})>"
