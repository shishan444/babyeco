"""Tests for Auth API endpoints."""

import pytest
from httpx import AsyncClient


class TestAuthEndpoints:
    """Test suite for auth API endpoints."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Should register a new user successfully."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900000001",
                "nickname": "TestUser",
                "password": "Password123!",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "user" in data

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        """Should login successfully."""
        # Register first
        await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900000002",
                "nickname": "LoginUser",
                "password": "Password123!",
            },
        )
        # Login
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "phone_number": "15900000002",
                "password": "Password123!",
            },
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    @pytest.mark.asyncio
    async def test_me_with_valid_token(self, client: AsyncClient):
        """Should return user info with valid token."""
        # Register
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900000003",
                "nickname": "MeUser",
                "password": "Password123!",
            },
        )
        token = reg.json()["access_token"]

        # Get /me
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["phone_number"] == "15900000003"

    @pytest.mark.asyncio
    async def test_refresh_token(self, client: AsyncClient):
        """Should refresh token successfully."""
        # Register
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900000004",
                "nickname": "RefreshUser",
                "password": "Password123!",
            },
        )
        token = reg.json()["access_token"]

        # Refresh
        response = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    @pytest.mark.asyncio
    async def test_login_wrong_password_fails(self, client: AsyncClient):
        """Should fail with wrong password."""
        await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900000005",
                "nickname": "WrongPassUser",
                "password": "CorrectPassword!",
            },
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "phone_number": "15900000005",
                "password": "WrongPassword!",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_duplicate_phone_fails(self, client: AsyncClient):
        """Should fail with duplicate phone number."""
        await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900000006",
                "nickname": "FirstUser",
                "password": "Password123!",
            },
        )
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900000006",
                "nickname": "SecondUser",
                "password": "Password456!",
            },
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_me_without_token_fails(self, client: AsyncClient):
        """Should fail without token."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token_fails(self, client: AsyncClient):
        """Should fail with invalid token."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user_fails(self, client: AsyncClient):
        """Should fail when login with non-existent user."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "phone_number": "19999999999",
                "password": "SomePassword!",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_register_with_avatar(self, client: AsyncClient):
        """Should register user with avatar."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "15900000010",
                "nickname": "AvatarUser",
                "password": "Password123!",
                "avatar": "https://example.com/avatar.png",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["avatar"] == "https://example.com/avatar.png"

    @pytest.mark.asyncio
    async def test_refresh_invalid_token_fails(self, client: AsyncClient):
        """Should fail when refreshing with invalid token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_register_missing_fields_fails(self, client: AsyncClient):
        """Should fail with missing required fields."""
        response = await client.post(
            "/api/v1/auth/register",
            json={"phone_number": "15900000011"},  # missing nickname and password
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_missing_fields_fails(self, client: AsyncClient):
        """Should fail with missing required fields."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"phone_number": "15900000012"},  # missing password
        )
        assert response.status_code == 422
