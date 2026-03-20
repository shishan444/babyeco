"""Tests for child profile API endpoints."""

import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.fixture
async def auth_headers(
    client: AsyncClient,
    sample_user_data: dict,
) -> dict:
    """Create authentication headers for testing."""
    # Register user
    await client.post("/api/v1/auth/register", json=sample_user_data)

    # Login and get token
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": sample_user_data["email"],
            "password": sample_user_data["password"],
        },
    )
    token = login_response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


class TestChildProfileCreation:
    """Tests for child profile creation."""

    @pytest.mark.asyncio
    async def test_create_child_profile_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_child_data: dict,
    ) -> None:
        """Test successful child profile creation."""
        response = await client.post(
            "/api/v1/children/",
            json=sample_child_data,
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == sample_child_data["name"]
        assert "invite_code" in data
        assert data["points_balance"] == 0
        assert data["device_bound"] is False

    @pytest.mark.asyncio
    async def test_create_child_profile_unauthorized(
        self,
        client: AsyncClient,
        sample_child_data: dict,
    ) -> None:
        """Test child profile creation without auth fails."""
        response = await client.post(
            "/api/v1/children/",
            json=sample_child_data,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_create_multiple_child_profiles(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_child_data: dict,
    ) -> None:
        """Test creating multiple child profiles for same parent."""
        # Create first child
        response1 = await client.post(
            "/api/v1/children/",
            json=sample_child_data,
            headers=auth_headers,
        )
        assert response1.status_code == status.HTTP_201_CREATED

        # Create second child with different name
        sample_child_data["name"] = "Second Child"
        response2 = await client.post(
            "/api/v1/children/",
            json=sample_child_data,
            headers=auth_headers,
        )
        assert response2.status_code == status.HTTP_201_CREATED


class TestChildProfileListing:
    """Tests for child profile listing."""

    @pytest.mark.asyncio
    async def test_list_child_profiles_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_child_data: dict,
    ) -> None:
        """Test listing child profiles for parent."""
        # Create a child profile first
        await client.post(
            "/api/v1/children/",
            json=sample_child_data,
            headers=auth_headers,
        )

        # List profiles
        response = await client.get("/api/v1/children/", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert data[0]["name"] == sample_child_data["name"]

    @pytest.mark.asyncio
    async def test_list_child_profiles_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ) -> None:
        """Test listing child profiles when none exist."""
        response = await client.get("/api/v1/children/", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0


class TestChildProfilePoints:
    """Tests for points management."""

    @pytest.mark.asyncio
    async def test_add_points_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_child_data: dict,
    ) -> None:
        """Test adding points to child profile."""
        # Create child profile
        create_response = await client.post(
            "/api/v1/children/",
            json=sample_child_data,
            headers=auth_headers,
        )
        profile_id = create_response.json()["id"]

        # Add points
        response = await client.post(
            f"/api/v1/children/{profile_id}/points?points=10",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["points_balance"] == 10
        assert data["total_points_earned"] == 10

    @pytest.mark.asyncio
    async def test_subtract_points_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_child_data: dict,
    ) -> None:
        """Test subtracting points from child profile."""
        # Create child profile
        create_response = await client.post(
            "/api/v1/children/",
            json=sample_child_data,
            headers=auth_headers,
        )
        profile_id = create_response.json()["id"]

        # Add points first
        await client.post(
            f"/api/v1/children/{profile_id}/points?points=50",
            headers=auth_headers,
        )

        # Subtract points
        response = await client.post(
            f"/api/v1/children/{profile_id}/points?points=-20",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["points_balance"] == 30

    @pytest.mark.asyncio
    async def test_subtract_points_insufficient(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_child_data: dict,
    ) -> None:
        """Test subtracting more points than available fails."""
        # Create child profile
        create_response = await client.post(
            "/api/v1/children/",
            json=sample_child_data,
            headers=auth_headers,
        )
        profile_id = create_response.json()["id"]

        # Try to subtract more than available
        response = await client.post(
            f"/api/v1/children/{profile_id}/points?points=-100",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
