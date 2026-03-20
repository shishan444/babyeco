"""Exchange system models for rewards, redemptions, and timer sessions."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.child_profile import ChildProfile


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


class Reward(Base, TimestampMixin):
    """Reward model for parent-defined rewards.

    @MX:ANCHOR
    Core reward entity for exchange system.
    Parents create rewards that children can exchange for points.
    """

    __tablename__ = "rewards"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    family_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[RewardType] = mapped_column(
        String(20),
        default=RewardType.ONE_TIME,
        nullable=False,
    )
    cost: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stock: Mapped[int | None] = mapped_column(Integer, nullable=True)
    initial_stock: Mapped[int | None] = mapped_column(Integer, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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
    redemptions: Mapped[list["Redemption"]] = relationship(back_populates="reward")
    timer_sessions: Mapped[list["TimerSession"]] = relationship(back_populates="reward")

    pinned_rewards: Mapped[list["PinnedReward"]] = relationship(back_populates="reward")

    def __repr__(self) -> str:
        return f"<Reward(id={self.id}, name={self.name}, type={self.type})>"


class Redemption(Base, TimestampMixin):
    """Redemption model for tracking reward exchanges.

    @MX:ANCHOR
    Core redemption entity tracking all reward exchanges.
    Records points spent and links to timer sessions.
    """

    __tablename__ = "redemptions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    child_id: Mapped[UUID] = mapped_column(
        ForeignKey("child_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reward_id: Mapped[UUID] = mapped_column(
        ForeignKey("rewards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    points_spent: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[RewardType] = mapped_column(String(20), nullable=False)
    status: Mapped[RedemptionStatus] = mapped_column(
        String(20),
        default=RedemptionStatus.COMPLETED,
        nullable=False,
        index=True,
    )
    redeemed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )
    timer_session_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("timer_sessions.id"),
        nullable=True,
    )

    # Relationships
    reward: Mapped["Reward"] = relationship(back_populates="redemptions")
    child: Mapped["ChildProfile"] = relationship(back_populates="redemptions")
    timer_session: Mapped["TimerSession | None"] = relationship(
        back_populates="redemption",
    )

    def __repr__(self) -> str:
        return f"<Redemption(id={self.id}, reward_id={self.reward_id})>"


class TimerSession(Base, TimestampMixin):
    """Timer session model for tracking active timers.

    @MX:NOTE
    Manages timer-based reward redemption sessions.
    Supports pause/resume functionality.
    """

    __tablename__ = "timer_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    child_id: Mapped[UUID] = mapped_column(
        ForeignKey("child_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reward_id: Mapped[UUID] = mapped_column(
        ForeignKey("rewards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    remaining_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[TimerSessionStatus] = mapped_column(
        String(20),
        default=TimerSessionStatus.RUNNING,
        nullable=False,
        index=True,
    )

    # Relationships
    reward: Mapped["Reward"] = relationship(back_populates="timer_sessions")
    child: Mapped["ChildProfile"] = relationship(back_populates="timer_sessions")
    redemption: Mapped["Redemption | None"] = relationship(
        back_populates="timer_session",
    )

    def __repr__(self) -> str:
        return f"<TimerSession(id={self.id}, status={self.status})>"


class PinnedReward(Base, TimestampMixin):
    """Pinned reward model for child's goal tracking.

    @MX:NOTE
    Allows children to pin a target reward for motivation.
    One pinned reward per child at a time.
    """

    __tablename__ = "pinned_rewards"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    child_id: Mapped[UUID] = mapped_column(
        ForeignKey("child_profiles.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    reward_id: Mapped[UUID] = mapped_column(
        ForeignKey("rewards.id", ondelete="CASCADE"),
        nullable=False,
    )
    pinned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    reward: Mapped["Reward"] = relationship(back_populates="pinned_rewards")
    child: Mapped["ChildProfile"] = relationship(back_populates="pinned_rewards")

    def __repr__(self) -> str:
        return f"<PinnedReward(child_id={self.child_id}, reward_id={self.reward_id})>"
