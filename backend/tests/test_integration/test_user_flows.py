"""Integration tests for complete user workflows."""

import pytest
from httpx import AsyncClient


class TestCompleteUserFlow:
    """Test complete user registration and child management workflow."""

    @pytest.mark.asyncio
    async def test_full_user_registration_and_child_management(self, client: AsyncClient):
        """Test complete flow: register -> login -> create children -> manage -> delete."""
        # Step 1: Register new user
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900009001",
                "nickname": "IntegrationUser",
                "password": "SecurePassword123!",
            },
        )
        assert register_response.status_code == 201
        register_data = register_response.json()
        assert "access_token" in register_data
        assert register_data["user"]["nickname"] == "IntegrationUser"

        token = register_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Step 2: Get user info
        me_response = await client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["phone_number"] == "15900009001"

        # Step 3: Create first child profile
        child1_response = await client.post(
            "/api/v1/children/",
            json={"child_name": "FirstChild", "child_age": 7},
            headers=headers,
        )
        assert child1_response.status_code == 201
        child1 = child1_response.json()
        assert child1["child_name"] == "FirstChild"
        assert child1["invite_code"].startswith("BABY-")

        # Step 4: Create second child profile
        child2_response = await client.post(
            "/api/v1/children/",
            json={"child_name": "SecondChild", "child_age": 9, "child_avatar": "https://example.com/avatar.png"},
            headers=headers,
        )
        assert child2_response.status_code == 201
        child2_id = child2_response.json()["id"]

        # Step 5: List all children
        list_response = await client.get("/api/v1/children/", headers=headers)
        assert list_response.status_code == 200
        children = list_response.json()
        assert len(children) == 2

        # Step 6: Update a child profile
        update_response = await client.patch(
            f"/api/v1/children/{child2_id}",
            json={"child_name": "UpdatedChild", "child_age": 10},
            headers=headers,
        )
        assert update_response.status_code == 200
        assert update_response.json()["child_name"] == "UpdatedChild"
        assert update_response.json()["child_age"] == 10

        # Step 7: Bind device using invite code
        invite_code = child1["invite_code"]
        bind_response = await client.post(
            "/api/v1/children/bind-device",
            json={"invite_code": invite_code, "device_id": "device-001", "device_token": "fcm-token"},
        )
        assert bind_response.status_code == 200
        assert bind_response.json()["device_id"] == "device-001"

        # Step 8: Refresh token
        refresh_response = await client.post("/api/v1/auth/refresh", headers=headers)
        assert refresh_response.status_code == 200
        new_token = refresh_response.json()["access_token"]
        # Token may be the same if refreshed within the same second, just verify it works
        assert new_token is not None

        # Step 9: Use new token to delete a child
        new_headers = {"Authorization": f"Bearer {new_token}"}
        delete_response = await client.delete(f"/api/v1/children/{child2_id}", headers=new_headers)
        assert delete_response.status_code == 204

        # Step 10: Verify only one child remains
        final_list_response = await client.get("/api/v1/children/", headers=new_headers)
        assert len(final_list_response.json()) == 1

    @pytest.mark.asyncio
    async def test_login_after_registration(self, client: AsyncClient):
        """Test that user can login after registration."""
        # Register
        await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900009002",
                "nickname": "LoginTestUser",
                "password": "MyPassword123!",
            },
        )

        # Login
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"phone_number": "15900009002", "password": "MyPassword123!"},
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data
        assert login_data["user"]["phone_number"] == "15900009002"

    @pytest.mark.asyncio
    async def test_invite_code_expiry_workflow(self, client: AsyncClient):
        """Test invite code generation and regeneration workflow."""
        # Register and create child
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900009003",
                "nickname": "InviteCodeUser",
                "password": "Password123!",
            },
        )
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create child
        child_response = await client.post(
            "/api/v1/children/",
            json={"child_name": "TestChild", "child_age": 8},
            headers=headers,
        )
        child_id = child_response.json()["id"]
        original_code = child_response.json()["invite_code"]

        # Regenerate invite code
        regen_response = await client.post(
            f"/api/v1/children/{child_id}/regenerate-invite",
            headers=headers,
        )
        assert regen_response.status_code == 200
        new_code = regen_response.json()["invite_code"]
        assert new_code != original_code
        assert new_code.startswith("BABY-")

        # Old code should no longer work
        old_code_bind = await client.post(
            "/api/v1/children/bind-device",
            json={"invite_code": original_code, "device_id": "device-old"},
        )
        assert old_code_bind.status_code == 400

        # New code should work
        new_code_bind = await client.post(
            "/api/v1/children/bind-device",
            json={"invite_code": new_code, "device_id": "device-new"},
        )
        assert new_code_bind.status_code == 200

    @pytest.mark.asyncio
    async def test_max_children_enforcement(self, client: AsyncClient):
        """Test that maximum 5 children per parent is enforced."""
        # Register
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900009004",
                "nickname": "MaxChildrenUser",
                "password": "Password123!",
            },
        )
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create 5 children (should succeed)
        for i in range(5):
            response = await client.post(
                "/api/v1/children/",
                json={"child_name": f"Child{i}", "child_age": 6 + i},
                headers=headers,
            )
            assert response.status_code == 201, f"Failed to create child {i}"

        # Try to create 6th child (should fail)
        response = await client.post(
            "/api/v1/children/",
            json={"child_name": "Child6", "child_age": 12},
            headers=headers,
        )
        assert response.status_code == 400
        assert "Maximum" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_isolation_between_users(self, client: AsyncClient):
        """Test that users cannot access each other's children."""
        # Register two users
        user1_reg = await client.post(
            "/api/v1/auth/register",
            json={"phone_number": "15900009005", "nickname": "User1", "password": "Password1!"},
        )
        user1_token = user1_reg.json()["access_token"]

        user2_reg = await client.post(
            "/api/v1/auth/register",
            json={"phone_number": "15900009006", "nickname": "User2", "password": "Password2!"},
        )
        user2_token = user2_reg.json()["access_token"]

        # User1 creates a child
        child_response = await client.post(
            "/api/v1/children/",
            json={"child_name": "User1Child", "child_age": 8},
            headers={"Authorization": f"Bearer {user1_token}"},
        )
        child_id = child_response.json()["id"]

        # User2 tries to access User1's child
        get_response = await client.get(
            f"/api/v1/children/{child_id}",
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        assert get_response.status_code == 404

        # User2 tries to update User1's child
        update_response = await client.patch(
            f"/api/v1/children/{child_id}",
            json={"child_name": "Hacked"},
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        assert update_response.status_code == 404

        # User2 tries to delete User1's child
        delete_response = await client.delete(
            f"/api/v1/children/{child_id}",
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        assert delete_response.status_code == 404

        # User2 should have no children
        list_response = await client.get(
            "/api/v1/children/",
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        assert list_response.json() == []


class TestHealthCheck:
    """Test health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Health check should return healthy status."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
