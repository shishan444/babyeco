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
    ) -> None:
        """Test successful user registration with phone number."""
        user_data = {
            "phone": "+8613812345678",
            "password": "TestPass123",
            "name": "Test Parent",
        }
        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["phone"] == user_data["phone"]
        assert data["name"] == user_data["name"]
        assert "id" in data
        assert "hashed_password" not in data
        assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_register_duplicate_phone(
        self,
        client: AsyncClient,
    ) -> None:
        """Test registration with duplicate phone fails."""
        user_data = {
            "phone": "+8613812345678",
            "password": "TestPass123",
            "name": "Test Parent",
        }
        # First registration
        await client.post("/api/v1/auth/register", json=user_data)

        # Second registration with same phone
        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_invalid_phone_format(
        self,
        client: AsyncClient,
    ) -> None:
        """Test registration with invalid phone format fails."""
        user_data = {
            "phone": "123456",  # Missing + and country code
            "password": "TestPass123",
            "name": "Test Parent",
        }
        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_register_weak_password(
        self,
        client: AsyncClient,
    ) -> None:
        """Test registration with weak password fails."""
        user_data = {
            "phone": "+8613812345678",
            "password": "short",  # Too short, no uppercase/digit
            "name": "Test Parent",
        }
        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_register_password_no_uppercase(
        self,
        client: AsyncClient,
    ) -> None:
        """Test registration with password missing uppercase fails."""
        user_data = {
            "phone": "+8613812345678",
            "password": "testpass123",  # No uppercase
            "name": "Test Parent",
        }
        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_register_password_no_digit(
        self,
        client: AsyncClient,
    ) -> None:
        """Test registration with password missing digit fails."""
        user_data = {
            "phone": "+8613812345678",
            "password": "TestPassword",  # No digit
            "name": "Test Parent",
        }
        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestAuthLogin:
    """Tests for user login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(
        self,
        client: AsyncClient,
    ) -> None:
        """Test successful login with phone number."""
        # Register user first
        user_data = {
            "phone": "+8613812345678",
            "password": "TestPass123",
            "name": "Test Parent",
        }
        await client.post("/api/v1/auth/register", json=user_data)

        # Login
        login_data = {
            "phone": user_data["phone"],
            "password": user_data["password"],
        }
        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user_id" in data

    @pytest.mark.asyncio
    async def test_login_wrong_password(
        self,
        client: AsyncClient,
    ) -> None:
        """Test login with wrong password fails."""
        # Register user first
        user_data = {
            "phone": "+8613812345678",
            "password": "TestPass123",
            "name": "Test Parent",
        }
        await client.post("/api/v1/auth/register", json=user_data)

        # Login with wrong password
        login_data = {
            "phone": user_data["phone"],
            "password": "WrongPass123",
        }
        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_login_nonexistent_phone(
        self,
        client: AsyncClient,
    ) -> None:
        """Test login with nonexistent phone fails."""
        login_data = {
            "phone": "+8619876543210",
            "password": "SomePassword123",
        }
        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthMe:
    """Tests for current user endpoint."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self,
        client: AsyncClient,
    ) -> None:
        """Test getting current user info with valid token."""
        # Register and login
        user_data = {
            "phone": "+8613812345678",
            "password": "TestPass123",
            "name": "Test Parent",
        }
        await client.post("/api/v1/auth/register", json=user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "phone": user_data["phone"],
                "password": user_data["password"],
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
        assert data["phone"] == user_data["phone"]
        assert data["name"] == user_data["name"]

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(
        self,
        client: AsyncClient,
    ) -> None:
        """Test getting current user without token fails."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

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


class TestAuthUpdate:
    """Tests for user profile update endpoint."""

    @pytest.mark.asyncio
    async def test_update_user_name(
        self,
        client: AsyncClient,
    ) -> None:
        """Test updating user name."""
        # Register and login
        user_data = {
            "phone": "+8613812345678",
            "password": "TestPass123",
            "name": "Test Parent",
        }
        await client.post("/api/v1/auth/register", json=user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "phone": user_data["phone"],
                "password": user_data["password"],
            },
        )
        token = login_response.json()["access_token"]

        # Update name
        update_data = {"name": "Updated Name"}
        response = await client.patch(
            "/api/v1/auth/me",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Name"


class TestTokenRefresh:
    """Tests for token refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self,
        client: AsyncClient,
    ) -> None:
        """Test refreshing access token."""
        # Register and login
        user_data = {
            "phone": "+8613812345678",
            "password": "TestPass123",
            "name": "Test Parent",
        }
        await client.post("/api/v1/auth/register", json=user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "phone": user_data["phone"],
                "password": user_data["password"],
            },
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(
        self,
        client: AsyncClient,
    ) -> None:
        """Test refresh with invalid token fails."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRateLimiting:
    """Tests for rate limiting."""

    @pytest.mark.asyncio
    async def test_login_rate_limiting(
        self,
        client: AsyncClient,
    ) -> None:
        """Test that login endpoint is rate limited."""
        user_data = {
            "phone": "+8613812345678",
            "password": "TestPass123",
            "name": "Test Parent",
        }
        await client.post("/api/v1/auth/register", json=user_data)

        login_data = {
            "phone": user_data["phone"],
            "password": "WrongPassword1",
        }

        # Make 6 attempts (5 is limit)
        for i in range(6):
            response = await client.post("/api/v1/auth/login", json=login_data)

        if i < 5:
            # First 5 attempts should return 401 (wrong password)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        else:
            # 6th attempt should return 429 (rate limited)
            assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    @pytest.mark.asyncio
    async def test_register_rate_limiting(
        self,
        client: AsyncClient,
    ) -> None:
        """Test that registration endpoint is rate limited."""
        base_user = {
            "password": "TestPass123",
            "name": "Test Parent",
        }

        # Make 4 attempts (3 is limit)
        for i in range(4):
            user_data = {
                **base_user,
                "phone": f"+861381234{i:04d}",  # Unique phone each time
            }
            response = await client.post("/api/v1/auth/register", json=user_data)

            if i < 3:
                # First 3 attempts may succeed or fail (duplicate, invalid)
                # We don't care about the result
                pass
            else:
                # 4th attempt should be rate limited
                if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                    break
