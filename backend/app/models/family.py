"""Family model for grouping parent and child accounts."""

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Family(Base, TimestampMixin):
    """Family model representing a household unit.

    @MX:ANCHOR
    Families group parents and children together in the BabyEco system.
    A family can have multiple parent accounts and multiple child profiles.
    This enables shared management of children's activities and rewards.

    @MX:NOTE
    Currently children are linked directly to parents via parent_id.
    The Family model provides an additional layer of organization for
    future features like family-wide settings, shared subscriptions, and
    multi-parent households.
    """

    __tablename__ = "families"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="My Family",
        comment="Family display name",
    )
    settings: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="Family-wide settings and preferences",
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="family",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Family(id={self.id}, name={self.name})>"
