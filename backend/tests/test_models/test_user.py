"""Tests for User model.

RED Phase: These tests define the expected behavior for the User model.
"""

import pytest
from uuid import UUID

from app.core.security import hash_password, verify_password
from app.models.user import User


class TestUserModel:
    """Test suite for User model."""

    def test_user_model_exists(self):
        """User model should be importable."""
        assert User is not None

    def test_user_has_phone_number(self):
        """User should have phone_number field."""
        assert hasattr(User, "phone_number")

    def test_user_has_nickname(self):
        """User should have nickname field."""
        assert hasattr(User, "nickname")

    def test_user_has_password_hash(self):
        """User should have password_hash field."""
        assert hasattr(User, "password_hash")

    def test_user_has_avatar(self):
        """User should have avatar field."""
        assert hasattr(User, "avatar")

    def test_user_has_is_active(self):
        """User should have is_active field."""
        assert hasattr(User, "is_active")


class TestUserCreation:
    """Test user creation functionality."""

    @pytest.mark.asyncio
    async def test_create_user_minimal(self, db_session):
        """Should create user with minimal required fields."""
        user = User(
            phone_number="13800138000",
            nickname="TestParent",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None
        assert user.phone_number == "13800138000"
        assert user.nickname == "TestParent"
        assert user.password_hash != "password123"  # Should be hashed

    @pytest.mark.asyncio
    async def test_create_user_with_avatar(self, db_session):
        """Should create user with optional avatar."""
        user = User(
            phone_number="13800138001",
            nickname="TestParent2",
            password_hash=hash_password("password123"),
            avatar="https://example.com/avatar.png",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.avatar == "https://example.com/avatar.png"

    @pytest.mark.asyncio
    async def test_user_default_is_active(self, db_session):
        """User should be active by default."""
        user = User(
            phone_number="13800138002",
            nickname="TestParent3",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.is_active is True


class TestUserPassword:
    """Test user password functionality."""

    def test_password_hashing(self):
        """Password should be hashed correctly."""
        plain_password = "SecurePassword123!"
        hashed = hash_password(plain_password)

        user = User(
            phone_number="13800138003",
            nickname="TestUser",
            password_hash=hashed,
        )

        assert user.password_hash != plain_password
        assert verify_password(plain_password, user.password_hash)

    def test_password_verification_wrong_password(self):
        """Should return False for wrong password."""
        user = User(
            phone_number="13800138004",
            nickname="TestUser",
            password_hash=hash_password("correct_password"),
        )

        assert not verify_password("wrong_password", user.password_hash)


class TestUserUniqueness:
    """Test user uniqueness constraints."""

    @pytest.mark.asyncio
    async def test_phone_number_unique(self, db_session):
        """Phone number should be unique."""
        user1 = User(
            phone_number="13800138005",
            nickname="User1",
            password_hash=hash_password("password123"),
        )
        db_session.add(user1)
        await db_session.commit()

        user2 = User(
            phone_number="13800138005",  # Same phone number
            nickname="User2",
            password_hash=hash_password("password456"),
        )
        db_session.add(user2)

        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()


class TestUserRelationships:
    """Test user relationships."""

    def test_user_has_children_relationship(self):
        """User should have children relationship for child profiles."""
        # Check relationship exists without accessing lazy-loaded data
        from sqlalchemy.orm import class_mapper

        mapper = class_mapper(User)
        relationship_names = [r.key for r in mapper.relationships]
        assert "children" in relationship_names
