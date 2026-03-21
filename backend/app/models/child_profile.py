"""Child profile model for child accounts."""

from datetime import date, datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class ChildProfileStatus(str, PyEnum):
    """Child profile status enumeration."""

    ACTIVE = "active"
    ARCHIVED = "archived"


class ChildProfile(Base, TimestampMixin):
    """Child profile model representing a child's account.

    @MX:ANCHOR
    Child profiles are linked to parent accounts and track
    points, tasks, and achievements for each child.

    @MX:NOTE
    Device binding: Each child profile can be bound to one device at a time.
    The device_id is set when a child logs in with the invite code.
    Device binding is enforced to prevent unauthorized access.
    """

    __tablename__ = "child_profiles"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    parent_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Device binding fields
    device_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
        comment="Unique device identifier for bound device",
    )
    device_bound_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when device was bound",
    )

    # Gamification fields
    points_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_points_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Invite code for device binding (6 characters, excluding confusing chars)
    invite_code: Mapped[str | None] = mapped_column(
        String(6),
        unique=True,
        nullable=True,
        index=True,
        comment="6-character invite code for device binding",
    )

    # Status tracking
    status: Mapped[ChildProfileStatus] = mapped_column(
        Enum(ChildProfileStatus),
        default=ChildProfileStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    # Legacy compatibility
    device_bound: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Legacy: True if device_id is set",
    )

    # Relationships
    parent: Mapped["User"] = relationship("User", back_populates="children")
    content_progress: Mapped[list["ContentProgress"]] = relationship(back_populates="child")
    content_unlocks: Mapped[list["ContentUnlock"]] = relationship(back_populates="child")
    redemptions: Mapped[list["Redemption"]] = relationship(back_populates="child")
    timer_sessions: Mapped[list["TimerSession"]] = relationship(back_populates="child")
    pinned_rewards: Mapped[list["PinnedReward"]] = relationship(back_populates="child")

    @property
    def age(self) -> int | None:
        """Calculate child's age from birth date.

        @MX:NOTE
        Returns None if birth_date is not set.
        Age is calculated as of current date.
        """
        if not self.birth_date:
            return None
        today = date.today()
        return (
            today.year
            - self.birth_date.year
            - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        )

    @property
    def is_device_bound(self) -> bool:
        """Check if a device is currently bound to this profile."""
        return self.device_id is not None

    @property
    def is_active(self) -> bool:
        """Check if this child profile is active.

        @MX:NOTE
        Returns True if status is active, False if archived.
        """
        return self.status == ChildProfileStatus.ACTIVE

    def bind_device(self, device_id: str) -> None:
        """Bind a device to this child profile.

        @MX:NOTE
        Sets device_id and device_bound_at, updates device_bound flag.
        Raises ValueError if a device is already bound.
        """
        if self.device_id:
            raise ValueError("Device already bound to this profile")
        self.device_id = device_id
        self.device_bound_at = datetime.now()
        self.device_bound = True

    def unbind_device(self) -> None:
        """Unbind the current device from this child profile."""
        self.device_id = None
        self.device_bound_at = None
        self.device_bound = False

    def __repr__(self) -> str:
        return (
            f"<ChildProfile(id={self.id}, name={self.name}, "
            f"points={self.points_balance}, device_bound={self.device_bound})>"
        )
