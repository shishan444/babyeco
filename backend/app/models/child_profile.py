"""Child profile model for managing children's accounts."""

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.core.security import generate_invite_code
from app.core.database import Base
from app.models.base import BaseMixin

if TYPE_CHECKING:
    from app.models.user import User


def _get_invite_code_expiry() -> datetime:
    """Get invite code expiry datetime (7 days from now, UTC, naive)."""
    return datetime.utcnow() + timedelta(days=settings.INVITE_CODE_EXPIRE_DAYS)


class ChildProfile(Base, BaseMixin):
    """Child profile model for child accounts.

    Attributes:
        id: UUID primary key
        child_name: Child's display name
        child_age: Child's age (6-12)
        child_avatar: Optional avatar URL
        invite_code: Unique invite code for device binding
        invite_code_expires_at: Expiration datetime for invite code
        points_balance: Current points balance
        device_id: Bound device identifier
        device_token: Device push notification token
        parent_id: Foreign key to parent user
        parent: Relationship to parent user
    """

    __tablename__ = "child_profiles"

    child_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    child_age: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    child_avatar: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    invite_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False,
        default=generate_invite_code,
    )
    invite_code_expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=_get_invite_code_expiry,
    )
    points_balance: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    device_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    device_token: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    parent_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    parent: Mapped["User"] = relationship(
        "User",
        back_populates="children",
    )

    def __repr__(self) -> str:
        return f"<ChildProfile {self.child_name} (age {self.child_age})>"

    def regenerate_invite_code(self) -> str:
        """Generate a new invite code and reset expiration.

        Returns:
            str: New invite code
        """
        self.invite_code = generate_invite_code()
        self.invite_code_expires_at = _get_invite_code_expiry()
        return self.invite_code

    def is_invite_code_valid(self) -> bool:
        """Check if invite code is still valid.

        Returns:
            bool: True if invite code is valid and not expired
        """
        if self.device_id is not None:
            # Already bound to a device
            return False
        return datetime.utcnow() < self.invite_code_expires_at

    def bind_device(self, device_id: str, device_token: str | None = None) -> None:
        """Bind a device to this child profile.

        Args:
            device_id: Unique device identifier
            device_token: Optional push notification token
        """
        self.device_id = device_id
        self.device_token = device_token
