"""User model for parent accounts."""

from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import BaseMixin

if TYPE_CHECKING:
    from app.models.child_profile import ChildProfile


class User(Base, BaseMixin):
    """User model representing a parent account.

    Attributes:
        id: UUID primary key
        phone_number: User's phone number (unique, used for login)
        nickname: Display name for the user
        password_hash: Bcrypt hashed password
        avatar: Optional avatar URL
        is_active: Whether the account is active
        children: List of child profiles belonging to this user
    """

    __tablename__ = "users"

    phone_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False,
    )
    nickname: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    avatar: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    children: Mapped[List["ChildProfile"]] = relationship(
        "ChildProfile",
        back_populates="parent",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User {self.nickname} ({self.phone_number})>"
