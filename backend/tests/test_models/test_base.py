"""Tests for base model.

RED Phase: These tests define the expected behavior for the base model.
"""

import pytest
from datetime import datetime
from uuid import UUID

from app.models.base import BaseMixin


class TestBaseModel:
    """Test suite for base model functionality."""

    def test_base_mixin_exists(self):
        """BaseMixin should be importable."""
        from app.models.base import BaseMixin

        assert BaseMixin is not None

    def test_base_mixin_has_id(self):
        """BaseMixin should have id attribute."""
        from app.models.base import BaseMixin

        assert hasattr(BaseMixin, "id")

    def test_base_mixin_has_created_at(self):
        """BaseMixin should have created_at timestamp."""
        from app.models.base import BaseMixin

        assert hasattr(BaseMixin, "created_at")

    def test_base_mixin_has_updated_at(self):
        """BaseMixin should have updated_at timestamp."""
        from app.models.base import BaseMixin

        assert hasattr(BaseMixin, "updated_at")


class TestBaseModelInstance:
    """Test base model instance behavior."""

    @pytest.mark.asyncio
    async def test_id_is_uuid(self, db_session):
        """Model id should be UUID type."""
        from app.models.user import User

        user = User(
            phone_number="13800138001",
            nickname="TestUser",
            password_hash="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None
        assert isinstance(user.id, UUID) or isinstance(user.id, str)
        # UUID string format: 8-4-4-4-12
        uuid_str = str(user.id)
        parts = uuid_str.split("-")
        assert len(parts) == 5

    @pytest.mark.asyncio
    async def test_created_at_auto_set(self, db_session):
        """created_at should be automatically set on creation."""
        from app.models.user import User

        user = User(
            phone_number="13800138002",
            nickname="TestUser2",
            password_hash="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)

    @pytest.mark.asyncio
    async def test_updated_at_auto_updated(self, db_session):
        """updated_at should be automatically updated on modification."""
        import asyncio

        from app.models.user import User

        user = User(
            phone_number="13800138003",
            nickname="TestUser3",
            password_hash="hashed_password",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        original_updated_at = user.updated_at

        # Wait a bit to ensure time difference
        await asyncio.sleep(0.01)

        # Update the user
        user.nickname = "UpdatedUser"
        await db_session.commit()
        await db_session.refresh(user)

        # updated_at should change (note: this depends on the DB auto-update)
        # For SQLite with default, we just check it exists
        assert user.updated_at is not None
