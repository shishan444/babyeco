"""Base model with common fields for all models."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BaseMixin:
    """Mixin providing common fields for all models.

    Provides:
        id: UUID primary key
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    id: Mapped[str] = mapped_column(
        TEXT,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TimestampMixin:
    """Mixin providing only timestamp fields."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
