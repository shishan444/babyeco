"""Tests for UserRepository.

RED Phase: These tests define the expected behavior for user repository.
"""

import pytest

from app.core.security import hash_password
from app.models.user import User
from app.repositories.user_repository import UserRepository


class TestUserRepository:
    """Test suite for UserRepository."""

    def test_user_repository_exists(self):
        """UserRepository should be importable."""
        assert UserRepository is not None

    def test_user_repository_has_create(self):
        """UserRepository should have create method."""
        repo = UserRepository(None)
        assert hasattr(repo, "create")

    def test_user_repository_has_get_by_id(self):
        """UserRepository should have get_by_id method."""
        repo = UserRepository(None)
        assert hasattr(repo, "get_by_id")

    def test_user_repository_has_get_by_phone(self):
        """UserRepository should have get_by_phone method."""
        repo = UserRepository(None)
        assert hasattr(repo, "get_by_phone")

    def test_user_repository_has_update(self):
        """UserRepository should have update method."""
        repo = UserRepository(None)
        assert hasattr(repo, "update")


class TestUserRepositoryCreate:
    """Test user repository create operation."""

    @pytest.mark.asyncio
    async def test_create_user(self, db_session):
        """Should create a new user."""
        repo = UserRepository(db_session)

        user_data = {
            "phone_number": "13800000001",
            "nickname": "NewUser",
            "password_hash": hash_password("password123"),
        }

        user = await repo.create(user_data)

        assert user.id is not None
        assert user.phone_number == "13800000001"
        assert user.nickname == "NewUser"

    @pytest.mark.asyncio
    async def test_create_user_with_avatar(self, db_session):
        """Should create user with avatar."""
        repo = UserRepository(db_session)

        user_data = {
            "phone_number": "13800000002",
            "nickname": "AvatarUser",
            "password_hash": hash_password("password123"),
            "avatar": "https://example.com/avatar.png",
        }

        user = await repo.create(user_data)

        assert user.avatar == "https://example.com/avatar.png"


class TestUserRepositoryGetById:
    """Test user repository get_by_id operation."""

    @pytest.mark.asyncio
    async def test_get_by_id_existing(self, db_session):
        """Should return user when ID exists."""
        repo = UserRepository(db_session)

        # Create a user first
        user = User(
            phone_number="13800000010",
            nickname="GetUser",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Get by ID
        found = await repo.get_by_id(user.id)

        assert found is not None
        assert found.id == user.id
        assert found.nickname == "GetUser"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, db_session):
        """Should return None when ID does not exist."""
        repo = UserRepository(db_session)

        found = await repo.get_by_id("non-existent-uuid")

        assert found is None


class TestUserRepositoryGetByPhone:
    """Test user repository get_by_phone operation."""

    @pytest.mark.asyncio
    async def test_get_by_phone_existing(self, db_session):
        """Should return user when phone number exists."""
        repo = UserRepository(db_session)

        # Create a user first
        user = User(
            phone_number="13800000020",
            nickname="PhoneUser",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()

        # Get by phone
        found = await repo.get_by_phone("13800000020")

        assert found is not None
        assert found.phone_number == "13800000020"
        assert found.nickname == "PhoneUser"

    @pytest.mark.asyncio
    async def test_get_by_phone_not_found(self, db_session):
        """Should return None when phone number does not exist."""
        repo = UserRepository(db_session)

        found = await repo.get_by_phone("99999999999")

        assert found is None


class TestUserRepositoryUpdate:
    """Test user repository update operation."""

    @pytest.mark.asyncio
    async def test_update_user_nickname(self, db_session):
        """Should update user nickname."""
        repo = UserRepository(db_session)

        # Create a user first
        user = User(
            phone_number="13800000030",
            nickname="OriginalName",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Update nickname
        updated = await repo.update(user.id, {"nickname": "UpdatedName"})

        assert updated is not None
        assert updated.nickname == "UpdatedName"

    @pytest.mark.asyncio
    async def test_update_user_avatar(self, db_session):
        """Should update user avatar."""
        repo = UserRepository(db_session)

        # Create a user first
        user = User(
            phone_number="13800000031",
            nickname="AvatarUser",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Update avatar
        updated = await repo.update(
            user.id,
            {"avatar": "https://example.com/new_avatar.png"},
        )

        assert updated is not None
        assert updated.avatar == "https://example.com/new_avatar.png"

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, db_session):
        """Should return None when updating non-existent user."""
        repo = UserRepository(db_session)

        updated = await repo.update("non-existent-uuid", {"nickname": "NewName"})

        assert updated is None

    @pytest.mark.asyncio
    async def test_update_user_is_active(self, db_session):
        """Should update user active status."""
        repo = UserRepository(db_session)

        # Create a user first
        user = User(
            phone_number="13800000032",
            nickname="ActiveUser",
            password_hash=hash_password("password123"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Deactivate user
        updated = await repo.update(user.id, {"is_active": False})

        assert updated is not None
        assert updated.is_active is False
