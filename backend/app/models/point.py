"""Point system models for tracking balances and transactions."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.child_profile import ChildProfile


class TransactionType(str, Enum):
    """Transaction type enumeration."""

    EARN = "earn"
    SPEND = "spend"
    FREEZE = "freeze"
    UNFREEZE = "unfreeze"
    ADJUST = "adjust"
    EXPIRATION = "expiration"


class PointBalance(Base, TimestampMixin):
    """Point balance model for child accounts.

    @MX:ANCHOR
    Primary balance tracking entity. One balance per child.
    Maintains running totals for earned and spent points.
    """

    __tablename__ = "point_balances"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    child_id: Mapped[UUID] = mapped_column(
        ForeignKey("child_profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    frozen: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_spent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    child: Mapped["ChildProfile"] = relationship("ChildProfile", backref="point_balance")

    @property
    def available(self) -> int:
        """Get available (non-frozen) balance."""
        return self.balance - self.frozen

    def __repr__(self) -> str:
        return f"<PointBalance(child_id={self.child_id}, balance={self.balance})>"


class PointFreeze(Base, TimestampMixin):
    """Point freeze model for holding reserved points.

    @MX:NOTE
    Allows parents to freeze points for specific rewards.
    Points are unavailable for spending until unfrozen.
    """

    __tablename__ = "point_freezes"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    child_id: Mapped[UUID] = mapped_column(
        ForeignKey("child_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=True)
    source_id: Mapped[UUID | None] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    released_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<PointFreeze(id={self.id}, amount={self.amount}, status={self.status})>"


class PointTransaction(Base, TimestampMixin):
    """Point transaction model for audit trail.

    @MX:ANCHOR
    Records all point movements with full audit trail.
    Supports earn, spend, freeze, unfreeze, adjust types.
    """

    __tablename__ = "point_transactions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    child_id: Mapped[UUID] = mapped_column(
        ForeignKey("child_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[TransactionType] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=True)
    source_id: Mapped[UUID | None] = mapped_column(String(36), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    # For freeze transactions, links to freeze record
    freeze_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("point_freezes.id"),
        nullable=True,
    )

    # Relationships
    child: Mapped["ChildProfile"] = relationship("ChildProfile", backref="transactions")
    freeze: Mapped["PointFreeze | None"] = relationship(
        "PointFreeze",
        backref="transactions",
    )

    def __repr__(self) -> str:
        return f"<PointTransaction(id={self.id}, type={self.type}, amount={self.amount})>"
