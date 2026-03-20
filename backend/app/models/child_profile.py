"""Child profile model for child accounts."""

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class ChildProfile(Base, TimestampMixin):
    """Child profile model representing a child's account.

    @MX:ANCHOR
    Child profiles are linked to parent accounts and track
    points, tasks, and achievements for each child.
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
    points_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_points_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    invite_code: Mapped[str | None] = mapped_column(String(10), unique=True, nullable=True)
    device_bound: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    parent: Mapped["User"] = relationship("User", back_populates="children")
    content_progress: Mapped[list["ContentProgress"]] = relationship(back_populates="child")
    content_unlocks: Mapped[list["ContentUnlock"]] = relationship(back_populates="child")
    redemptions: Mapped[list["Redemption"]] = relationship(back_populates="child")
    timer_sessions: Mapped[list["TimerSession"]] = relationship(back_populates="child")
    pinned_rewards: Mapped[list["PinnedReward"]] = relationship(back_populates="child")

    @property
    def age(self) -> int | None:
        """Calculate child's age from birth date."""
        if not self.birth_date:
            return None
        today = date.today()
        return (
            today.year
            - self.birth_date.year
            - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        )

    def __repr__(self) -> str:
        return f"<ChildProfile(id={self.id}, name={self.name}, points={self.points_balance})>"
