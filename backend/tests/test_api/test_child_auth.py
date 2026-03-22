"""Tests for child device authentication API endpoints."""

import pytest
from fastapi import status
from httpx import AsyncClient


class TestChildDeviceBinding:
    """Tests for child device binding endpoints."""

    @pytest.mark.asyncio
    async def test_bind_device_with_invite_code(
        self,
        client: AsyncClient,
        sample_user_data: dict,
        sample_child_data: dict,
    ) -> None:
        """Test binding a device using invite code."""
        # Register parent and create child profile
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "phone": sample_user_data["phone"],
                "password": sample_user_data["password"],
            },
        )
        token = login_response.json()["access_token"]

        # Create child profile
        child_response = await client.post(
            "/api/v1/children/",
            json=sample_child_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        child_profile = child_response.json()
        invite_code = child_profile["invite_code"]

        # Bind device
        bind_request = {
            "invite_code": invite_code,
            "device_id": "test-device-123",
        }
        response = await client.post(
            "/api/v1/child/bind",
            json=bind_request,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["device_id"] == "test-device-123"
        assert data["device_bound"] is True

    @pytest.mark.asyncio
    async def test_bind_device_invalid_code(
        self,
        client: AsyncClient,
    ) -> None:
        """Test binding with invalid invite code fails."""
        bind_request = {
            "invite_code": "INVALID",
            "device_id": "test-device-123",
        }
        response = await client.post(
            "/api/v1/child/bind",
            json=bind_request,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_bind_device_already_bound_to_another(
        self,
        client: AsyncClient,
        sample_user_data: dict,
        sample_child_data: dict,
    ) -> None:
        """Test binding device already bound to another profile fails."""
        # Register parent and create child profiles
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "phone": sample_user_data["phone"],
                "password": sample_user_data["password"],
            },
        )
        token = login_response.json()["access_token"]

        # Create two child profiles
        child1_response = await client.post(
            "/api/v1/children/",
            json={**sample_child_data, "name": "Child 1"},
            headers={"Authorization": f"Bearer {token}"},
        )
        invite_code_1 = child1_response.json()["invite_code"]

        child2_response = await client.post(
            "/api/v1/children/",
            json={**sample_child_data, "name": "Child 2"},
            headers={"Authorization": f"Bearer {token}"},
        )
        invite_code_2 = child2_response.json()["invite_code"]

        # Bind device to first child
        await client.post(
            "/api/v1/child/bind",
            json={
                "invite_code": invite_code_1,
                "device_id": "test-device-123",
            },
        )

        # Try to bind same device to second child
        response = await client.post(
            "/api/v1/child/bind",
            json={
                "invite_code": invite_code_2,
                "device_id": "test-device-123",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already bound" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_bind_device_profile_already_has_device(
        self,
        client: AsyncClient,
        sample_user_data: dict,
        sample_child_data: dict,
    ) -> None:
        """Test binding a second device to same profile fails."""
        # Register parent and create child profile
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "phone": sample_user_data["phone"],
                "password": sample_user_data["password"],
            },
        )
        token = login_response.json()["access_token"]

        # Create child profile
        child_response = await client.post(
            "/api/v1/children/",
            json=sample_child_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        invite_code = child_response.json()["invite_code"]

        # Bind first device
        await client.post(
            "/api/v1/child/bind",
            json={
                "invite_code": invite_code,
                "device_id": "device-1",
            },
        )

        # Try to bind second device
        response = await client.post(
            "/api/v1/child/bind",
            json={
                "invite_code": invite_code,
                "device_id": "device-2",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already has a device bound" in response.json()["detail"].lower()


class TestChildLogin:
    """Tests for child login endpoint."""

    @pytest.mark.asyncio
    async def test_child_login_success(
        self,
        client: AsyncClient,
        sample_user_data: dict,
        sample_child_data: dict,
    ) -> None:
        """Test successful child login with invite code."""
        # Register parent and create child profile
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "phone": sample_user_data["phone"],
                "password": sample_user_data["password"],
            },
        )
        token = login_response.json()["access_token"]

        # Create child profile
        child_response = await client.post(
            "/api/v1/children/",
            json=sample_child_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        invite_code = child_response.json()["invite_code"]

        # Child login (binds device automatically)
        login_request = {
            "invite_code": invite_code,
            "device_id": "child-device-123",
        }
        response = await client.post(
            "/api/v1/child/login",
            json=login_request,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["name"] == sample_child_data["name"]

    @pytest.mark.asyncio
    async def test_child_login_invalid_code(
        self,
        client: AsyncClient,
    ) -> None:
        """Test child login with invalid invite code fails."""
        login_request = {
            "invite_code": "INVALID",
            "device_id": "child-device-123",
        }
        response = await client.post(
            "/api/v1/child/login",
            json=login_request,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_child_login_wrong_device(
        self,
        client: AsyncClient,
        sample_user_data: dict,
        sample_child_data: dict,
    ) -> None:
        """Test child login with wrong device fails."""
        # Register parent and create child profile
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "phone": sample_user_data["phone"],
                "password": sample_user_data["password"],
            },
        )
        token = login_response.json()["access_token"]

        # Create child profile
        child_response = await client.post(
            "/api/v1/children/",
            json=sample_child_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        invite_code = child_response.json()["invite_code"]

        # Bind first device
        await client.post(
            "/api/v1/child/login",
            json={
                "invite_code": invite_code,
                "device_id": "device-1",
            },
        )

        # Try to login with different device
        response = await client.post(
            "/api/v1/child/login",
            json={
                "invite_code": invite_code,
                "device_id": "device-2",
            },
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "different device" in response.json()["detail"].lower()


class TestInviteCodeManagement:
    """Tests for invite code management endpoints."""

    @pytest.mark.asyncio
    async def test_get_invite_code(
        self,
        client: AsyncClient,
        sample_user_data: dict,
        sample_child_data: dict,
    ) -> None:
        """Test getting invite code for child profile."""
        # Register parent and create child profile
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "phone": sample_user_data["phone"],
                "password": sample_user_data["password"],
            },
        )
        token = login_response.json()["access_token"]

        # Create child profile
        child_response = await client.post(
            "/api/v1/children/",
            json=sample_child_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        child_profile = child_response.json()
        profile_id = child_profile["id"]

        # Get invite code
        response = await client.get(
            f"/api/v1/children/{profile_id}/invite-code",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "invite_code" in data
        assert len(data["invite_code"]) == 6

    @pytest.mark.asyncio
    async def test_regenerate_invite_code(
        self,
        client: AsyncClient,
        sample_user_data: dict,
        sample_child_data: dict,
    ) -> None:
        """Test regenerating invite code."""
        # Register parent and create child profile
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "phone": sample_user_data["phone"],
                "password": sample_user_data["password"],
            },
        )
        token = login_response.json()["access_token"]

        # Create child profile
        child_response = await client.post(
            "/api/v1/children/",
            json=sample_child_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        child_profile = child_response.json()
        profile_id = child_profile["id"]
        old_invite_code = child_profile["invite_code"]

        # Regenerate invite code
        response = await client.post(
            f"/api/v1/children/{profile_id}/regenerate-code",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["invite_code"] != old_invite_code
        assert len(data["invite_code"]) == 6
