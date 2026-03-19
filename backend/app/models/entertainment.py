"""Entertainment content models for children's reading and tracking."""

from datetime import datetime, date
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.child_profile import ChildProfile


class ContentCategory(str, Enum):
    """Content category enumeration."""

    STORY = "story"
    VIDEO = "video"
    AUDIO = "audio"
    ARTICLE = "article"


    GAME = "game"


class ContentStatus(str, Enum):
    """Content status enumeration."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ContentType(str, Enum):
    """Content type enumeration."""

    FREE = "free"
    PREMIUM = "premium"


    UNLOCKABLE = "unlockable"


class Content(Base, TimestampMixin):
    """Content model for educational and entertainment content.

    @MX:ANCHOR
    Core content entity for entertainment system.
    Stores various types of content for children.
    """

    __tablename__ = "contents"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    family_id: Mapped[UUID] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_url: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[ContentCategory] = mapped_column(
        String(20),
        default=ContentCategory.STORY,
        nullable=False,
        index=True,
    )
    type: Mapped[ContentType] = mapped_column(
        String(20),
        default=ContentType.FREE,
        nullable=False,
    )
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    age_min: Mapped[int | = mapped_column(Integer, nullable=True)
    age_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ContentStatus] = mapped_column(
        String(20),
        default=ContentStatus.PUBLISHED,
        nullable=False,
        index=True,
    )
    points_cost: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    points_reward: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    author: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    progress: Mapped[list["ContentProgress"]] = relationship(back_populates="content_progress")

    unlocks: Mapped[list["ContentUnlock"]] = relationship(back_populates="content_unlocks")

    questions: Mapped[list["ContentQuestion"]] = relationship(back_populates="content_questions")

    def __repr__(self) -> str:
        return f"<Content(id={self.id}, title={self.title})>"


class ContentProgress(Base, TimestampMixin):
    """Content progress model for tracking reading progress.

    @MX:NOTE
    Tracks each child's progress through content.
    Supports resume, functionality.
    """

    __tablename__ = "content_progress"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    child_id: Mapped[UUID] = mapped_column(
        ForeignKey("child_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content_id: Mapped[UUID] = mapped_column(
        ForeignKey("contents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    progress_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    points_earned: Mapped[int | = mapped_column(Integer, default=0, nullable=False)
    last_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        onupdate=datetime.utcnow,
    )

    # Relationships
    content: Mapped["Content"] = relationship(back_populates="content")
    child: Mapped["ChildProfile"] = relationship(back_populates="child_profiles")

    def __repr__(self) -> str:
        return f"<ContentProgress(id={self.id}, progress={self.progress_seconds}s>"


class ContentUnlock(Base, TimestampMixin):
    """Content unlock model for premium content purchases.

    @MX:NOTE
    Records when premium content is unlocked by a child.
    """

    __tablename__ = "content_unlocks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    child_id: Mapped[UUID] = mapped_column(
        ForeignKey("child_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content_id: Mapped[UUID] = mapped_column(
        ForeignKey("contents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    points_spent: Mapped[int] = mapped_column(Integer, nullable=False)
    unlocked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    content: Mapped["Content"] = relationship(back_populates="content")
    child: Mapped["ChildProfile"] = relationship(back_populates="child_profiles")

    def __repr__(self) -> str:
        return f"<ContentUnlock(id={self.id})>"


class ContentQuestion(Base, TimestampMixin):
    """Content question model for AI-generated questions.

    @MX:NOTE
    Stores AI-generated questions for completed content.
    Linked to point bonus rewards.
    """

    __tablename__ = "content_questions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    content_id: Mapped[UUID] = mapped_column(
        ForeignKey("contents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[str | None] = mapped_column(Text, nullable=True)
    correct_answer: Mapped[int | None = mapped_column(Integer, nullable=True)
    points_bonus: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    content: Mapped["Content"] = relationship(back_populates="content")
    progress_records: Mapped[list["ContentProgress"]] = relationship(back_populates="progress")

    def __repr__(self) -> str:
        return f"<ContentQuestion(id={self.id}, question={self.question_text[:30[:30_options})>"


