"""Tests for ChildProfileService.

RED Phase: These tests define the expected behavior for child profile service.
"""

import pytest

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User
from app.schemas.child_profile import (
    ChildProfileCreateRequest,
    ChildProfileUpdateRequest,
    DeviceBindRequest,
)
from app.services.child_profile_service import ChildProfileService


@pytest.fixture
async def parent_user(db_session):
    """Create a parent user for testing."""
    user = User(
        phone_number="13600000001",
        nickname="TestParent",
        password_hash=hash_password("password123"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestChildProfileService:
    """Test suite for ChildProfileService."""

    def test_child_profile_service_exists(self):
        """ChildProfileService should be importable."""
        assert ChildProfileService is not None

    def test_child_profile_service_has_create_profile(self):
        """ChildProfileService should have create_profile method."""
        service = ChildProfileService(None)
        assert hasattr(service, "create_profile")

    def test_child_profile_service_has_get_profiles(self):
        """ChildProfileService should have get_profiles method."""
        service = ChildProfileService(None)
        assert hasattr(service, "get_profiles")

    def test_child_profile_service_has_update_profile(self):
        """ChildProfileService should have update_profile method."""
        service = ChildProfileService(None)
        assert hasattr(service, "update_profile")

    def test_child_profile_service_has_delete_profile(self):
        """ChildProfileService should have delete_profile method."""
        service = ChildProfileService(None)
        assert hasattr(service, "delete_profile")

    def test_child_profile_service_has_bind_device(self):
        """ChildProfileService should have bind_device method."""
        service = ChildProfileService(None)
        assert hasattr(service, "bind_device")


class TestChildProfileServiceCreate:
    """Test child profile service create operation."""

    @pytest.mark.asyncio
    async def test_create_profile_success(self, db_session, parent_user):
        """Should create a child profile successfully."""
        service = ChildProfileService(db_session)

        request = ChildProfileCreateRequest(
            child_name="TestChild",
            child_age=8,
            child_avatar="https://example.com/child.png",
        )

        profile = await service.create_profile(parent_user.id, request)

        assert profile is not None
        assert profile.child_name == "TestChild"
        assert profile.child_age == 8
        assert profile.invite_code.startswith("BABY-")
        assert profile.points_balance == 0

    @pytest.mark.asyncio
    async def test_create_profile_generates_invite_code(self, db_session, parent_user):
        """Should generate invite code for new profile."""
        service = ChildProfileService(db_session)

        request = ChildProfileCreateRequest(
            child_name="InviteChild",
            child_age=10,
        )

        profile = await service.create_profile(parent_user.id, request)

        assert profile.invite_code is not None
        assert len(profile.invite_code) == 13  # BABY- (5) + 8 chars


class TestChildProfileServiceGetProfiles:
    """Test child profile service get_profiles operation."""

    @pytest.mark.asyncio
    async def test_get_profiles_returns_all(self, db_session, parent_user):
        """Should return all profiles for a parent."""
        from app.repositories.child_profile_repository import ChildProfileRepository

        repo = ChildProfileRepository(db_session)
        service = ChildProfileService(db_session)

        # Create profiles
        for i in range(3):
            await repo.create({
                "child_name": f"Child{i}",
                "child_age": 6 + i,
                "parent_id": parent_user.id,
            })

        profiles = await service.get_profiles(parent_user.id)

        assert len(profiles) == 3

    @pytest.mark.asyncio
    async def test_get_profiles_empty(self, db_session, parent_user):
        """Should return empty list when no profiles."""
        service = ChildProfileService(db_session)

        profiles = await service.get_profiles(parent_user.id)

        assert profiles == []


class TestChildProfileServiceUpdate:
    """Test child profile service update operation."""

    @pytest.mark.asyncio
    async def test_update_profile_name(self, db_session, parent_user):
        """Should update child profile name."""
        from app.repositories.child_profile_repository import ChildProfileRepository

        repo = ChildProfileRepository(db_session)
        service = ChildProfileService(db_session)

        # Create profile
        profile = await repo.create({
            "child_name": "OriginalName",
            "child_age": 7,
            "parent_id": parent_user.id,
        })

        # Update
        request = ChildProfileUpdateRequest(child_name="UpdatedName")
        updated = await service.update_profile(profile.id, parent_user.id, request)

        assert updated is not None
        assert updated.child_name == "UpdatedName"

    @pytest.mark.asyncio
    async def test_update_profile_not_found(self, db_session, parent_user):
        """Should return None when profile not found."""
        service = ChildProfileService(db_session)

        request = ChildProfileUpdateRequest(child_name="NewName")
        updated = await service.update_profile("non-existent-id", parent_user.id, request)

        assert updated is None


class TestChildProfileServiceDelete:
    """Test child profile service delete operation."""

    @pytest.mark.asyncio
    async def test_delete_profile_success(self, db_session, parent_user):
        """Should delete child profile."""
        from app.repositories.child_profile_repository import ChildProfileRepository

        repo = ChildProfileRepository(db_session)
        service = ChildProfileService(db_session)

        # Create profile
        profile = await repo.create({
            "child_name": "ToDelete",
            "child_age": 8,
            "parent_id": parent_user.id,
        })

        # Delete
        deleted = await service.delete_profile(profile.id, parent_user.id)

        assert deleted is True

        # Verify deleted
        found = await repo.get_by_id(profile.id)
        assert found is None

    @pytest.mark.asyncio
    async def test_delete_profile_not_found(self, db_session, parent_user):
        """Should return False when profile not found."""
        service = ChildProfileService(db_session)

        deleted = await service.delete_profile("non-existent-id", parent_user.id)

        assert deleted is False


class TestChildProfileServiceBindDevice:
    """Test child profile service bind_device operation."""

    @pytest.mark.asyncio
    async def test_bind_device_success(self, db_session, parent_user):
        """Should bind device to child profile."""
        from app.repositories.child_profile_repository import ChildProfileRepository

        repo = ChildProfileRepository(db_session)
        service = ChildProfileService(db_session)

        # Create profile
        profile = await repo.create({
            "child_name": "DeviceChild",
            "child_age": 9,
            "parent_id": parent_user.id,
        })

        # Bind device
        request = DeviceBindRequest(
            invite_code=profile.invite_code,
            device_id="device-123",
            device_token="push-token-456",
        )

        result = await service.bind_device(request)

        assert result is not None
        assert result.device_id == "device-123"
        assert result.device_token == "push-token-456"

    @pytest.mark.asyncio
    async def test_bind_device_invalid_invite_code(self, db_session):
        """Should return None for invalid invite code."""
        service = ChildProfileService(db_session)

        request = DeviceBindRequest(
            invite_code="BABY-INVALID",
            device_id="device-123",
        )

        result = await service.bind_device(request)

        assert result is None


class TestChildProfileServiceLimit:
    """Test child profile service limit enforcement."""

    @pytest.mark.asyncio
    async def test_max_profiles_limit_enforced(self, db_session, parent_user):
        """Should enforce max 5 profiles per parent."""
        from app.repositories.child_profile_repository import ChildProfileRepository

        repo = ChildProfileRepository(db_session)
        service = ChildProfileService(db_session)

        # Create 5 profiles (max limit)
        for i in range(settings.MAX_CHILDREN_PER_PARENT):
            await repo.create({
                "child_name": f"Child{i}",
                "child_age": 6 + i,
                "parent_id": parent_user.id,
            })

        # Try to create 6th profile
        request = ChildProfileCreateRequest(
            child_name="SixthChild",
            child_age=10,
        )

        with pytest.raises(ValueError, match="5"):
            await service.create_profile(parent_user.id, request)

    @pytest.mark.asyncio
    async def test_can_create_up_to_limit(self, db_session, parent_user):
        """Should allow creating up to max limit."""
        from app.repositories.child_profile_repository import ChildProfileRepository

        repo = ChildProfileRepository(db_session)
        service = ChildProfileService(db_session)

        # Create 4 profiles
        for i in range(4):
            await repo.create({
                "child_name": f"Child{i}",
                "child_age": 6 + i,
                "parent_id": parent_user.id,
            })

        # Create 5th profile should succeed
        request = ChildProfileCreateRequest(
            child_name="FifthChild",
            child_age=10,
        )

        profile = await service.create_profile(parent_user.id, request)
        assert profile is not None
