"""Report and analytics models for tracking child progress.

@MX:NOTE
This module provides data aggregation and caching for reports.
Achievements and milestones track gamification progress.
"""

from datetime import date, datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.child_profile import ChildProfile
    from app.models.user import User


class ExportStatus(str, PyEnum):
    """Report export status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AchievementCategory(str, PyEnum):
    """Achievement category enumeration."""

    STREAK = "streak"
    POINTS = "points"
    TASKS = "tasks"
    SPECIAL = "special"


class MilestoneType(str, PyEnum):
    """Milestone type enumeration."""

    POINTS = "points"
    TASKS = "tasks"
    STREAK = "streak"


class CachedAggregate(Base, TimestampMixin):
    """Cached aggregated data for performance optimization.

    @MX:NOTE
    Caches pre-computed aggregates to avoid expensive queries.
    Invalidated on data changes via cache keys.
    """

    __tablename__ = "cached_aggregates"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    child_id: Mapped[UUID] = mapped_column(
        ForeignKey("child_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    aggregate_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="daily_tasks, weekly_points, monthly_summary, etc.",
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    data: Mapped[dict] = mapped_column(Text, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    child: Mapped["ChildProfile"] = relationship("ChildProfile", backref="cached_aggregates")

    def __repr__(self) -> str:
        return f"<CachedAggregate(id={self.id}, type={self.aggregate_type}, child_id={self.child_id})>"


class ReportExport(Base, TimestampMixin):
    """Report export model for async report generation.

    @MX:NOTE
    Tracks export job status for PDF/CSV generation.
    Downloadable links stored in file_url when complete.
    """

    __tablename__ = "report_exports"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    family_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requested_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    child_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("child_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    format: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="pdf, csv",
    )
    sections: Mapped[list[str]] = mapped_column(
        Text,
        nullable=False,
        comment="JSON array of report sections",
    )
    date_range_start: Mapped[date] = mapped_column(Date, nullable=False)
    date_range_end: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[ExportStatus] = mapped_column(
        String(20),
        default=ExportStatus.PENDING,
        nullable=False,
        index=True,
    )
    file_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    family: Mapped["User"] = relationship("User", foreign_keys=[family_id])
    requester: Mapped["User"] = relationship("User", foreign_keys=[requested_by])

    def __repr__(self) -> str:
        return f"<ReportExport(id={self.id}, status={self.status}, format={self.format})>"


class Achievement(Base, TimestampMixin):
    """Achievement model for gamification badges.

    @MX:ANCHOR
    Achievement definitions and unlock tracking.
    Children unlock achievements by meeting criteria.
    """

    __tablename__ = "achievements"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    child_id: Mapped[UUID] = mapped_column(
        ForeignKey("child_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    achievement_key: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="streak-3, points-100, etc.",
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    icon: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[AchievementCategory] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    unlocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    unlocked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    progress: Mapped[float] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Progress percentage 0-100",
    )

    # Relationships
    child: Mapped["ChildProfile"] = relationship("ChildProfile", backref="achievements")

    def __repr__(self) -> str:
        return f"<Achievement(id={self.id}, key={self.achievement_key}, unlocked={self.unlocked})>"


class Milestone(Base, TimestampMixin):
    """Milestone model for tracking major accomplishments.

    @MX:NOTE
    Milestones represent significant progress markers.
    Auto-unlocked when thresholds are reached.
    """

    __tablename__ = "milestones"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    child_id: Mapped[UUID] = mapped_column(
        ForeignKey("child_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[MilestoneType] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    threshold: Mapped[int] = mapped_column(Integer, nullable=False)
    achieved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    achieved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    child: Mapped["ChildProfile"] = relationship("ChildProfile", backref="milestones")

    def __repr__(self) -> str:
        return f"<Milestone(id={self.id}, title={self.title}, achieved={self.achieved})>"
