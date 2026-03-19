"""Tests for authentication API endpoints."""

import pytest
from fastapi import status
from httpx import AsyncClient


class TestAuthRegistration:
    """Tests for user registration endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(
        self,
        client: AsyncClient,
        sample_user_data: dict,
    ) -> None:
        """Test successful user registration."""
        response = await client.post("/api/v1/auth/register", json=sample_user_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["name"] == sample_user_data["name"]
        assert "id" in data
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(
        self,
        client: AsyncClient,
        sample_user_data: dict,
    ) -> None:
        """Test registration with duplicate email fails."""
        # First registration
        await client.post("/api/v1/auth/register", json=sample_user_data)

        # Second registration with same email
        response = await client.post("/api/v1/auth/register", json=sample_user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_invalid_email(
        self,
        client: AsyncClient,
        sample_user_data: dict,
    ) -> None:
        """Test registration with invalid email fails."""
        sample_user_data["email"] = "invalid-email"
        response = await client.post("/api/v1/auth/register", json=sample_user_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_register_weak_password(
        self,
        client: AsyncClient,
        sample_user_data: dict,
    ) -> None:
        """Test registration with weak password fails."""
        sample_user_data["password"] = "short"
        response = await client.post("/api/v1/auth/register", json=sample_user_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestAuthLogin:
    """Tests for user login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(
        self,
        client: AsyncClient,
        sample_user_data: dict,
    ) -> None:
        """Test successful login."""
        # Register user first
        await client.post("/api/v1/auth/register", json=sample_user_data)

        # Login
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"],
        }
        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(
        self,
        client: AsyncClient,
        sample_user_data: dict,
    ) -> None:
        """Test login with wrong password fails."""
        # Register user first
        await client.post("/api/v1/auth/register", json=sample_user_data)

        # Login with wrong password
        login_data = {
            "email": sample_user_data["email"],
            "password": "WrongPassword123!",
        }
        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(
        self,
        client: AsyncClient,
    ) -> None:
        """Test login with nonexistent user fails."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "SomePassword123!",
        }
        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthMe:
    """Tests for current user endpoint."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self,
        client: AsyncClient,
        sample_user_data: dict,
    ) -> None:
        """Test getting current user info with valid token."""
        # Register and login
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": sample_user_data["email"],
                "password": sample_user_data["password"],
            },
        )
        token = login_response.json()["access_token"]

        # Get current user
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == sample_user_data["email"]

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(
        self,
        client: AsyncClient,
    ) -> None:
        """Test getting current user without token fails."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(
        self,
        client: AsyncClient,
    ) -> None:
        """Test getting current user with invalid token fails."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
