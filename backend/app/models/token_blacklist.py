"""Token blacklist model for logout functionality."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TokenBlacklist(Base):
    """Token blacklist for invalidated JWT tokens.

    @MX:NOTE
    When a user logs out, their refresh token is added to this blacklist
    to prevent further use. Tokens are automatically cleaned up after expiration.
    """

    __tablename__ = "token_blacklist"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    token_jti: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="JWT ID (jti claim) to identify the token",
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User ID who owned this token",
    )
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="When the token was revoked",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="When the token would expire (for cleanup)",
    )

    # Relationship
    user: Mapped["User"] = relationship("User")

    @property
    def is_valid(self) -> bool:
        """Check if the blacklisted token is still within its expiration period."""
        return datetime.now(timezone.utc) < self.expires_at

    def __repr__(self) -> str:
        return f"<TokenBlacklist(jti={self.token_jti[:8]}..., user_id={self.user_id})>"
