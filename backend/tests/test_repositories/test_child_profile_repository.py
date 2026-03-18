"""Tests for ChildProfileRepository.

RED Phase: These tests define the expected behavior for child profile repository.
"""

import pytest

from app.core.security import hash_password
from app.models.child_profile import ChildProfile
from app.models.user import User
from app.repositories.child_profile_repository import ChildProfileRepository


class TestChildProfileRepository:
    """Test suite for ChildProfileRepository."""

    def test_child_profile_repository_exists(self):
        """ChildProfileRepository should be importable."""
        assert ChildProfileRepository is not None

    def test_child_profile_repository_has_create(self):
        """ChildProfileRepository should have create method."""
        repo = ChildProfileRepository(None)
        assert hasattr(repo, "create")

    def test_child_profile_repository_has_get_by_id(self):
        """ChildProfileRepository should have get_by_id method."""
        repo = ChildProfileRepository(None)
        assert hasattr(repo, "get_by_id")

    def test_child_profile_repository_has_get_by_parent(self):
        """ChildProfileRepository should have get_by_parent method."""
        repo = ChildProfileRepository(None)
        assert hasattr(repo, "get_by_parent")

    def test_child_profile_repository_has_get_by_invite_code(self):
        """ChildProfileRepository should have get_by_invite_code method."""
        repo = ChildProfileRepository(None)
        assert hasattr(repo, "get_by_invite_code")

    def test_child_profile_repository_has_count_by_parent(self):
        """ChildProfileRepository should have count_by_parent method."""
        repo = ChildProfileRepository(None)
        assert hasattr(repo, "count_by_parent")


class TestChildProfileRepositoryCreate:
    """Test child profile repository create operation."""

    @pytest.mark.asyncio
    async def test_create_child_profile(self, db_session):
        """Should create a new child profile."""
        # Create parent first
        user = User(
            phone_number="13900000001",
            nickname="Parent",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        repo = ChildProfileRepository(db_session)

        child_data = {
            "child_name": "TestChild",
            "child_age": 8,
            "parent_id": user.id,
        }

        child = await repo.create(child_data)

        assert child.id is not None
        assert child.child_name == "TestChild"
        assert child.child_age == 8

    @pytest.mark.asyncio
    async def test_create_child_profile_with_avatar(self, db_session):
        """Should create child profile with avatar."""
        user = User(
            phone_number="13900000002",
            nickname="Parent2",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        repo = ChildProfileRepository(db_session)

        child_data = {
            "child_name": "AvatarChild",
            "child_age": 10,
            "child_avatar": "https://example.com/child.png",
            "parent_id": user.id,
        }

        child = await repo.create(child_data)

        assert child.child_avatar == "https://example.com/child.png"


class TestChildProfileRepositoryGetById:
    """Test child profile repository get_by_id operation."""

    @pytest.mark.asyncio
    async def test_get_by_id_existing(self, db_session):
        """Should return child profile when ID exists."""
        user = User(
            phone_number="13900000010",
            nickname="Parent10",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        child = ChildProfile(
            child_name="GetChild",
            child_age=7,
            parent_id=user.id,
        )
        db_session.add(child)
        await db_session.commit()
        await db_session.refresh(child)

        repo = ChildProfileRepository(db_session)
        found = await repo.get_by_id(child.id)

        assert found is not None
        assert found.id == child.id
        assert found.child_name == "GetChild"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, db_session):
        """Should return None when ID does not exist."""
        repo = ChildProfileRepository(db_session)

        found = await repo.get_by_id("non-existent-uuid")

        assert found is None


class TestChildProfileRepositoryGetByParent:
    """Test child profile repository get_by_parent operation."""

    @pytest.mark.asyncio
    async def test_get_by_parent_returns_children(self, db_session):
        """Should return all children for a parent."""
        user = User(
            phone_number="13900000020",
            nickname="Parent20",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create multiple children
        for i in range(3):
            child = ChildProfile(
                child_name=f"Child{i}",
                child_age=6 + i,
                parent_id=user.id,
            )
            db_session.add(child)
        await db_session.commit()

        repo = ChildProfileRepository(db_session)
        children = await repo.get_by_parent(user.id)

        assert len(children) == 3
        assert all(c.parent_id == user.id for c in children)

    @pytest.mark.asyncio
    async def test_get_by_parent_empty(self, db_session):
        """Should return empty list when parent has no children."""
        user = User(
            phone_number="13900000021",
            nickname="ParentNoChildren",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        repo = ChildProfileRepository(db_session)
        children = await repo.get_by_parent(user.id)

        assert children == []


class TestChildProfileRepositoryGetByInviteCode:
    """Test child profile repository get_by_invite_code operation."""

    @pytest.mark.asyncio
    async def test_get_by_invite_code_existing(self, db_session):
        """Should return child profile when invite code exists."""
        user = User(
            phone_number="13900000030",
            nickname="Parent30",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        child = ChildProfile(
            child_name="InviteChild",
            child_age=9,
            parent_id=user.id,
        )
        db_session.add(child)
        await db_session.commit()
        await db_session.refresh(child)

        repo = ChildProfileRepository(db_session)
        found = await repo.get_by_invite_code(child.invite_code)

        assert found is not None
        assert found.invite_code == child.invite_code

    @pytest.mark.asyncio
    async def test_get_by_invite_code_not_found(self, db_session):
        """Should return None when invite code does not exist."""
        repo = ChildProfileRepository(db_session)

        found = await repo.get_by_invite_code("BABY-NOTEXIST")

        assert found is None


class TestChildProfileRepositoryCountByParent:
    """Test child profile repository count_by_parent operation."""

    @pytest.mark.asyncio
    async def test_count_by_parent_with_children(self, db_session):
        """Should return correct count of children."""
        user = User(
            phone_number="13900000040",
            nickname="Parent40",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create 4 children
        for i in range(4):
            child = ChildProfile(
                child_name=f"CountChild{i}",
                child_age=6 + i,
                parent_id=user.id,
            )
            db_session.add(child)
        await db_session.commit()

        repo = ChildProfileRepository(db_session)
        count = await repo.count_by_parent(user.id)

        assert count == 4

    @pytest.mark.asyncio
    async def test_count_by_parent_empty(self, db_session):
        """Should return 0 when parent has no children."""
        user = User(
            phone_number="13900000041",
            nickname="ParentEmpty",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        repo = ChildProfileRepository(db_session)
        count = await repo.count_by_parent(user.id)

        assert count == 0


class TestChildProfileRepositoryUpdate:
    """Test child profile repository update operation."""

    @pytest.mark.asyncio
    async def test_update_child_profile(self, db_session):
        """Should update child profile."""
        user = User(
            phone_number="13900000050",
            nickname="Parent50",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        child = ChildProfile(
            child_name="UpdateChild",
            child_age=7,
            parent_id=user.id,
        )
        db_session.add(child)
        await db_session.commit()
        await db_session.refresh(child)

        repo = ChildProfileRepository(db_session)
        updated = await repo.update(child.id, {"child_age": 8})

        assert updated is not None
        assert updated.child_age == 8

    @pytest.mark.asyncio
    async def test_update_child_profile_bind_device(self, db_session):
        """Should update child profile device binding."""
        user = User(
            phone_number="13900000051",
            nickname="Parent51",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        child = ChildProfile(
            child_name="DeviceChild",
            child_age=8,
            parent_id=user.id,
        )
        db_session.add(child)
        await db_session.commit()
        await db_session.refresh(child)

        repo = ChildProfileRepository(db_session)
        updated = await repo.update(
            child.id,
            {"device_id": "device123", "device_token": "token123"},
        )

        assert updated is not None
        assert updated.device_id == "device123"
        assert updated.device_token == "token123"


class TestChildProfileRepositoryDelete:
    """Test child profile repository delete operation."""

    @pytest.mark.asyncio
    async def test_delete_child_profile(self, db_session):
        """Should delete child profile."""
        user = User(
            phone_number="13900000060",
            nickname="Parent60",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        child = ChildProfile(
            child_name="DeleteChild",
            child_age=7,
            parent_id=user.id,
        )
        db_session.add(child)
        await db_session.commit()
        await db_session.refresh(child)
        child_id = child.id

        repo = ChildProfileRepository(db_session)
        deleted = await repo.delete(child_id)

        assert deleted is True

        # Verify deleted
        found = await repo.get_by_id(child_id)
        assert found is None

    @pytest.mark.asyncio
    async def test_delete_child_profile_not_found(self, db_session):
        """Should return False when deleting non-existent profile."""
        repo = ChildProfileRepository(db_session)

        deleted = await repo.delete("non-existent-uuid")

        assert deleted is False
