"""User model for parent accounts."""

from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.child_profile import ChildProfile
    from app.models.family import Family


class UserStatus(str, PyEnum):
    """User account status enumeration."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class UserRole(str, PyEnum):
    """User role enumeration."""

    PARENT = "parent"
    ADMIN = "admin"


class User(Base, TimestampMixin):
    """User model representing a parent account.

    @MX:ANCHOR
    Primary user entity for the BabyEco system.
    Parents can have multiple child profiles linked to their account.
    Uses phone number (E.164 format) as primary identifier for authentication.
    """

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    phone: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False,
        comment="E.164 format phone number",
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus),
        default=UserStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last successful login timestamp",
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        default=UserRole.PARENT,
        nullable=False,
    )

    # Legacy fields (optional, for future email support)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Family relationship
    family_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("families.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Optional family ID for household grouping",
    )

    # Relationships
    family: Mapped["Family"] = relationship(
        "Family",
        back_populates="users",
        lazy="selectin",
    )
    children: Mapped[list["ChildProfile"]] = relationship(
        "ChildProfile",
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def is_active(self) -> bool:
        """Check if user account is active."""
        return self.status == UserStatus.ACTIVE

    def __repr__(self) -> str:
        return f"<User(id={self.id}, phone={self.phone}, name={self.name}, status={self.status.value})>"
