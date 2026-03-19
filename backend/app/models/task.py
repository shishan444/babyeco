"""Task model for child tasks and assignments."""

from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.child_profile import ChildProfile


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


class Task(Base, TimestampMixin):
    """Task model for child tasks and assignments.

    @MX:ANCHOR
    Primary task entity for the BabyEco system.
    Parents create tasks, children complete them to earn points.
    """

    __tablename__ = "tasks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    child_id: Mapped[UUID] = mapped_column(
        ForeignKey("child_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[TaskCategory] = mapped_column(
        SQLEnum(TaskCategory),
        default=TaskCategory.DAILY,
        nullable=False,
    )
    points: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus),
        default=TaskStatus.PENDING,
        nullable=False,
        index=True,
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_time: Mapped[str | None] = mapped_column(String(5), nullable=True)  # HH:MM format
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recurrence_pattern: Mapped[str | None] = mapped_column(String(50), nullable=True)  # cron-like
    streak_bonus: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    child: Mapped["ChildProfile"] = relationship("ChildProfile", backref="tasks")

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title={self.title}, status={self.status})>"


class TaskCompletion(Base, TimestampMixin):
    """Task completion record for tracking history and streaks.

    @MX:NOTE
    Tracks each task completion for analytics and streak calculation.
    """

    __tablename__ = "task_completions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    child_id: Mapped[UUID] = mapped_column(
        ForeignKey("child_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    completed_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    points_earned: Mapped[int] = mapped_column(Integer, nullable=False)
    streak_day: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    def __repr__(self) -> str:
        return f"<TaskCompletion(id={self.id}, task_id={self.task_id})>"
