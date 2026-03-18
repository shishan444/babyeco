"""Tests for Children API endpoints."""

import pytest
from httpx import AsyncClient


class TestChildrenEndpoints:
    """Test suite for children API endpoints."""

    @pytest.mark.asyncio
    async def test_create_child_profile_success(self, client: AsyncClient):
        """Should create a child profile successfully."""
        # Register parent first
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900001001",
                "nickname": "Parent1",
                "password": "Password123!",
            },
        )
        token = reg.json()["access_token"]

        # Create child profile
        response = await client.post(
            "/api/v1/children/",
            json={
                "child_name": "Child1",
                "child_age": 8,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["child_name"] == "Child1"
        assert data["child_age"] == 8
        assert "invite_code" in data
        assert data["invite_code"].startswith("BABY-")

    @pytest.mark.asyncio
    async def test_get_children_list_success(self, client: AsyncClient):
        """Should get list of children for parent."""
        # Register parent
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900001002",
                "nickname": "Parent2",
                "password": "Password123!",
            },
        )
        token = reg.json()["access_token"]

        # Create two children
        await client.post(
            "/api/v1/children/",
            json={"child_name": "Child1", "child_age": 7},
            headers={"Authorization": f"Bearer {token}"},
        )
        await client.post(
            "/api/v1/children/",
            json={"child_name": "Child2", "child_age": 9},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Get list
        response = await client.get(
            "/api/v1/children/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["child_name"] == "Child1"
        assert data[1]["child_name"] == "Child2"

    @pytest.mark.asyncio
    async def test_get_child_profile_by_id(self, client: AsyncClient):
        """Should get a specific child profile by ID."""
        # Register parent
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900001003",
                "nickname": "Parent3",
                "password": "Password123!",
            },
        )
        token = reg.json()["access_token"]

        # Create child
        create = await client.post(
            "/api/v1/children/",
            json={"child_name": "ChildToGet", "child_age": 6},
            headers={"Authorization": f"Bearer {token}"},
        )
        child_id = create.json()["id"]

        # Get by ID
        response = await client.get(
            f"/api/v1/children/{child_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["child_name"] == "ChildToGet"

    @pytest.mark.asyncio
    async def test_update_child_profile(self, client: AsyncClient):
        """Should update a child profile."""
        # Register parent
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900001004",
                "nickname": "Parent4",
                "password": "Password123!",
            },
        )
        token = reg.json()["access_token"]

        # Create child
        create = await client.post(
            "/api/v1/children/",
            json={"child_name": "OldName", "child_age": 6},
            headers={"Authorization": f"Bearer {token}"},
        )
        child_id = create.json()["id"]

        # Update
        response = await client.patch(
            f"/api/v1/children/{child_id}",
            json={"child_name": "NewName", "child_age": 7},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["child_name"] == "NewName"
        assert response.json()["child_age"] == 7

    @pytest.mark.asyncio
    async def test_delete_child_profile(self, client: AsyncClient):
        """Should delete a child profile."""
        # Register parent
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900001005",
                "nickname": "Parent5",
                "password": "Password123!",
            },
        )
        token = reg.json()["access_token"]

        # Create child
        create = await client.post(
            "/api/v1/children/",
            json={"child_name": "ChildToDelete", "child_age": 6},
            headers={"Authorization": f"Bearer {token}"},
        )
        child_id = create.json()["id"]

        # Delete
        response = await client.delete(
            f"/api/v1/children/{child_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 204

        # Verify deleted
        get_response = await client.get(
            f"/api/v1/children/{child_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_bind_device_success(self, client: AsyncClient):
        """Should bind device to child profile."""
        # Register parent
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900001006",
                "nickname": "Parent6",
                "password": "Password123!",
            },
        )
        token = reg.json()["access_token"]

        # Create child
        create = await client.post(
            "/api/v1/children/",
            json={"child_name": "ChildWithDevice", "child_age": 8},
            headers={"Authorization": f"Bearer {token}"},
        )
        invite_code = create.json()["invite_code"]

        # Bind device (no auth required - uses invite code)
        response = await client.post(
            "/api/v1/children/bind-device",
            json={
                "invite_code": invite_code,
                "device_id": "device-123",
                "device_token": "fcm-token-456",
            },
        )
        assert response.status_code == 200
        assert response.json()["device_id"] == "device-123"

    @pytest.mark.asyncio
    async def test_max_children_limit(self, client: AsyncClient):
        """Should enforce max 5 children per parent."""
        # Register parent
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900001007",
                "nickname": "Parent7",
                "password": "Password123!",
            },
        )
        token = reg.json()["access_token"]

        # Create 5 children
        for i in range(5):
            response = await client.post(
                "/api/v1/children/",
                json={"child_name": f"Child{i}", "child_age": 6 + i},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 201

        # 6th should fail
        response = await client.post(
            "/api/v1/children/",
            json={"child_name": "Child6", "child_age": 10},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_child_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent child."""
        # Register parent
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900001008",
                "nickname": "Parent8",
                "password": "Password123!",
            },
        )
        token = reg.json()["access_token"]

        # Get non-existent child
        response = await client.get(
            "/api/v1/children/non-existent-id",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_unauthorized_access_fails(self, client: AsyncClient):
        """Should fail without authorization token."""
        response = await client.get("/api/v1/children/")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_regenerate_invite_code(self, client: AsyncClient):
        """Should regenerate invite code for child profile."""
        # Register parent
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900001009",
                "nickname": "Parent9",
                "password": "Password123!",
            },
        )
        token = reg.json()["access_token"]

        # Create child
        create = await client.post(
            "/api/v1/children/",
            json={"child_name": "ChildRegen", "child_age": 7},
            headers={"Authorization": f"Bearer {token}"},
        )
        child_id = create.json()["id"]
        old_code = create.json()["invite_code"]

        # Regenerate invite code
        response = await client.post(
            f"/api/v1/children/{child_id}/regenerate-invite",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        new_code = response.json()["invite_code"]
        assert new_code != old_code
        assert new_code.startswith("BABY-")

    @pytest.mark.asyncio
    async def test_update_other_parent_child_fails(self, client: AsyncClient):
        """Should fail when trying to update another parent's child."""
        # Register two parents
        reg1 = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900001010",
                "nickname": "Parent10",
                "password": "Password123!",
            },
        )
        token1 = reg1.json()["access_token"]

        reg2 = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900001011",
                "nickname": "Parent11",
                "password": "Password123!",
            },
        )
        token2 = reg2.json()["access_token"]

        # Create child with parent1
        create = await client.post(
            "/api/v1/children/",
            json={"child_name": "Parent1Child", "child_age": 8},
            headers={"Authorization": f"Bearer {token1}"},
        )
        child_id = create.json()["id"]

        # Try to update with parent2 (should fail)
        response = await client.patch(
            f"/api/v1/children/{child_id}",
            json={"child_name": "HackedName"},
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_other_parent_child_fails(self, client: AsyncClient):
        """Should fail when trying to delete another parent's child."""
        # Register two parents
        reg1 = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900001012",
                "nickname": "Parent12",
                "password": "Password123!",
            },
        )
        token1 = reg1.json()["access_token"]

        reg2 = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900001013",
                "nickname": "Parent13",
                "password": "Password123!",
            },
        )
        token2 = reg2.json()["access_token"]

        # Create child with parent1
        create = await client.post(
            "/api/v1/children/",
            json={"child_name": "Parent1Child", "child_age": 8},
            headers={"Authorization": f"Bearer {token1}"},
        )
        child_id = create.json()["id"]

        # Try to delete with parent2 (should fail)
        response = await client.delete(
            f"/api/v1/children/{child_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_bind_device_invalid_invite_code(self, client: AsyncClient):
        """Should fail with invalid invite code."""
        response = await client.post(
            "/api/v1/children/bind-device",
            json={
                "invite_code": "BABY-INVALID",
                "device_id": "device-123",
            },
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_child_with_avatar(self, client: AsyncClient):
        """Should create child profile with avatar."""
        # Register parent
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900001014",
                "nickname": "Parent14",
                "password": "Password123!",
            },
        )
        token = reg.json()["access_token"]

        # Create child with avatar
        response = await client.post(
            "/api/v1/children/",
            json={
                "child_name": "ChildWithAvatar",
                "child_age": 9,
                "child_avatar": "https://example.com/child.png",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        assert response.json()["child_avatar"] == "https://example.com/child.png"

    @pytest.mark.asyncio
    async def test_regenerate_invite_nonexistent_child(self, client: AsyncClient):
        """Should fail when regenerating invite for non-existent child."""
        # Register parent
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900001015",
                "nickname": "Parent15",
                "password": "Password123!",
            },
        )
        token = reg.json()["access_token"]

        # Try to regenerate invite for non-existent child
        response = await client.post(
            "/api/v1/children/non-existent-id/regenerate-invite",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_child_not_found(self, client: AsyncClient):
        """Should return 404 when updating non-existent child."""
        # Register parent
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900001016",
                "nickname": "Parent16",
                "password": "Password123!",
            },
        )
        token = reg.json()["access_token"]

        # Try to update non-existent child
        response = await client.patch(
            "/api/v1/children/non-existent-id",
            json={"child_name": "NewName"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_child_not_found(self, client: AsyncClient):
        """Should return 404 when deleting non-existent child."""
        # Register parent
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900001017",
                "nickname": "Parent17",
                "password": "Password123!",
            },
        )
        token = reg.json()["access_token"]

        # Try to delete non-existent child
        response = await client.delete(
            "/api/v1/children/non-existent-id",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_other_parent_child_fails(self, client: AsyncClient):
        """Should fail when getting another parent's child."""
        # Register two parents
        reg1 = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900001018",
                "nickname": "Parent18",
                "password": "Password123!",
            },
        )
        token1 = reg1.json()["access_token"]

        reg2 = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900001019",
                "nickname": "Parent19",
                "password": "Password123!",
            },
        )
        token2 = reg2.json()["access_token"]

        # Create child with parent1
        create = await client.post(
            "/api/v1/children/",
            json={"child_name": "Parent1Child", "child_age": 8},
            headers={"Authorization": f"Bearer {token1}"},
        )
        child_id = create.json()["id"]

        # Try to get with parent2 (should fail)
        response = await client.get(
            f"/api/v1/children/{child_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_regenerate_invite_other_parent_child_fails(self, client: AsyncClient):
        """Should fail when regenerating invite for another parent's child."""
        # Register two parents
        reg1 = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900001020",
                "nickname": "Parent20",
                "password": "Password123!",
            },
        )
        token1 = reg1.json()["access_token"]

        reg2 = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900001021",
                "nickname": "Parent21",
                "password": "Password123!",
            },
        )
        token2 = reg2.json()["access_token"]

        # Create child with parent1
        create = await client.post(
            "/api/v1/children/",
            json={"child_name": "Parent1Child", "child_age": 8},
            headers={"Authorization": f"Bearer {token1}"},
        )
        child_id = create.json()["id"]

        # Try to regenerate invite with parent2 (should fail)
        response = await client.post(
            f"/api/v1/children/{child_id}/regenerate-invite",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code == 404
