"""Tests for ChildProfile model.

RED Phase: These tests define the expected behavior for the ChildProfile model.
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.core.config import settings
from app.core.security import hash_password
from app.models.child_profile import ChildProfile
from app.models.user import User


class TestChildProfileModel:
    """Test suite for ChildProfile model."""

    def test_child_profile_model_exists(self):
        """ChildProfile model should be importable."""
        assert ChildProfile is not None

    def test_child_profile_has_child_name(self):
        """ChildProfile should have child_name field."""
        assert hasattr(ChildProfile, "child_name")

    def test_child_profile_has_child_age(self):
        """ChildProfile should have child_age field."""
        assert hasattr(ChildProfile, "child_age")

    def test_child_profile_has_child_avatar(self):
        """ChildProfile should have child_avatar field."""
        assert hasattr(ChildProfile, "child_avatar")

    def test_child_profile_has_invite_code(self):
        """ChildProfile should have invite_code field."""
        assert hasattr(ChildProfile, "invite_code")

    def test_child_profile_has_invite_code_expires_at(self):
        """ChildProfile should have invite_code_expires_at field."""
        assert hasattr(ChildProfile, "invite_code_expires_at")

    def test_child_profile_has_points_balance(self):
        """ChildProfile should have points_balance field."""
        assert hasattr(ChildProfile, "points_balance")

    def test_child_profile_has_device_id(self):
        """ChildProfile should have device_id field."""
        assert hasattr(ChildProfile, "device_id")

    def test_child_profile_has_device_token(self):
        """ChildProfile should have device_token field."""
        assert hasattr(ChildProfile, "device_token")

    def test_child_profile_has_parent_id(self):
        """ChildProfile should have parent_id field."""
        assert hasattr(ChildProfile, "parent_id")


class TestChildProfileCreation:
    """Test child profile creation functionality."""

    @pytest.mark.asyncio
    async def test_create_child_profile_minimal(self, db_session):
        """Should create child profile with minimal required fields."""
        # Create parent user first
        user = User(
            phone_number="13900139000",
            nickname="Parent",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        child = ChildProfile(
            child_name="TestChild",
            child_age=8,
            parent_id=user.id,
        )
        db_session.add(child)
        await db_session.commit()
        await db_session.refresh(child)

        assert child.id is not None
        assert child.child_name == "TestChild"
        assert child.child_age == 8
        assert child.invite_code.startswith("BABY-")
        assert child.points_balance == 0

    @pytest.mark.asyncio
    async def test_create_child_profile_with_avatar(self, db_session):
        """Should create child profile with optional avatar."""
        user = User(
            phone_number="13900139001",
            nickname="Parent2",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        child = ChildProfile(
            child_name="TestChild2",
            child_age=10,
            child_avatar="https://example.com/child.png",
            parent_id=user.id,
        )
        db_session.add(child)
        await db_session.commit()
        await db_session.refresh(child)

        assert child.child_avatar == "https://example.com/child.png"

    @pytest.mark.asyncio
    async def test_invite_code_auto_generated(self, db_session):
        """Invite code should be auto-generated on creation."""
        user = User(
            phone_number="13900139002",
            nickname="Parent3",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        child = ChildProfile(
            child_name="TestChild3",
            child_age=7,
            parent_id=user.id,
        )
        db_session.add(child)
        await db_session.commit()
        await db_session.refresh(child)

        assert child.invite_code is not None
        assert child.invite_code.startswith("BABY-")
        assert len(child.invite_code) == 13  # BABY- (5) + 8 chars

    @pytest.mark.asyncio
    async def test_invite_code_expiry_auto_set(self, db_session):
        """Invite code expiry should be auto-set to 7 days from creation."""
        user = User(
            phone_number="13900139003",
            nickname="Parent4",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        child = ChildProfile(
            child_name="TestChild4",
            child_age=9,
            parent_id=user.id,
        )
        db_session.add(child)
        await db_session.commit()
        await db_session.refresh(child)

        expected_expiry = datetime.utcnow() + timedelta(
            days=settings.INVITE_CODE_EXPIRE_DAYS
        )
        # Allow 1 minute tolerance
        diff = abs((child.invite_code_expires_at - expected_expiry).total_seconds())
        assert diff < 60  # Within 1 minute


class TestChildProfileAgeValidation:
    """Test child profile age validation."""

    @pytest.mark.asyncio
    async def test_age_within_valid_range(self, db_session):
        """Age should be valid between 6-12."""
        user = User(
            phone_number="13900139010",
            nickname="ParentAge",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        for age in [6, 8, 10, 12]:
            child = ChildProfile(
                child_name=f"Child{age}",
                child_age=age,
                parent_id=user.id,
            )
            db_session.add(child)
            await db_session.commit()
            await db_session.refresh(child)
            assert child.child_age == age


class TestChildProfileInviteCodeMethods:
    """Test invite code methods."""

    @pytest.mark.asyncio
    async def test_regenerate_invite_code(self, db_session):
        """regenerate_invite_code should generate new code and reset expiry."""
        user = User(
            phone_number="13900139020",
            nickname="ParentRegen",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        child = ChildProfile(
            child_name="TestChildRegen",
            child_age=8,
            parent_id=user.id,
        )
        db_session.add(child)
        await db_session.commit()
        await db_session.refresh(child)

        original_code = child.invite_code
        original_expiry = child.invite_code_expires_at

        new_code = child.regenerate_invite_code()
        await db_session.commit()
        await db_session.refresh(child)

        assert new_code != original_code
        assert child.invite_code == new_code
        assert child.invite_code_expires_at > original_expiry

    @pytest.mark.asyncio
    async def test_is_invite_code_valid_when_valid(self, db_session):
        """is_invite_code_valid should return True for valid unbound codes."""
        user = User(
            phone_number="13900139021",
            nickname="ParentValid",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        child = ChildProfile(
            child_name="TestChildValid",
            child_age=8,
            parent_id=user.id,
        )
        db_session.add(child)
        await db_session.commit()
        await db_session.refresh(child)

        assert child.is_invite_code_valid() is True

    @pytest.mark.asyncio
    async def test_is_invite_code_valid_when_bound(self, db_session):
        """is_invite_code_valid should return False when device is bound."""
        user = User(
            phone_number="13900139022",
            nickname="ParentBound",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        child = ChildProfile(
            child_name="TestChildBound",
            child_age=8,
            parent_id=user.id,
        )
        db_session.add(child)
        await db_session.commit()
        await db_session.refresh(child)

        child.bind_device("device123", "token123")
        await db_session.commit()

        assert child.is_invite_code_valid() is False


class TestChildProfileDeviceBinding:
    """Test device binding functionality."""

    @pytest.mark.asyncio
    async def test_bind_device(self, db_session):
        """bind_device should set device_id and device_token."""
        user = User(
            phone_number="13900139030",
            nickname="ParentDevice",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        child = ChildProfile(
            child_name="TestChildDevice",
            child_age=8,
            parent_id=user.id,
        )
        db_session.add(child)
        await db_session.commit()
        await db_session.refresh(child)

        assert child.device_id is None
        assert child.device_token is None

        child.bind_device("device_abc123", "push_token_xyz")
        await db_session.commit()
        await db_session.refresh(child)

        assert child.device_id == "device_abc123"
        assert child.device_token == "push_token_xyz"


class TestChildProfileRelationships:
    """Test child profile relationships."""

    def test_child_profile_has_parent_relationship(self):
        """ChildProfile should have parent relationship."""
        from sqlalchemy.orm import class_mapper

        mapper = class_mapper(ChildProfile)
        relationship_names = [r.key for r in mapper.relationships]
        assert "parent" in relationship_names

    @pytest.mark.asyncio
    async def test_parent_relationship_works(self, db_session):
        """Parent relationship should return the associated user."""
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select

        user = User(
            phone_number="13900139040",
            nickname="ParentRel",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        child = ChildProfile(
            child_name="TestChildRel",
            child_age=8,
            parent_id=user.id,
        )
        db_session.add(child)
        await db_session.commit()

        # Query with eager loading
        result = await db_session.execute(
            select(ChildProfile)
            .where(ChildProfile.id == child.id)
            .options(selectinload(ChildProfile.parent))
        )
        loaded_child = result.scalar_one()

        assert loaded_child.parent is not None
        assert loaded_child.parent.id == user.id
        assert loaded_child.parent.nickname == "ParentRel"
