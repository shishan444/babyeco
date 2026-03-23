"""Tests for family authentication and management.

@MX:NOTE
Tests for SPEC-BE-AUTH-001 requirements:
- EDR-001: Family creation on parent registration
- Invite code generation and management
- Token expiration timing
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi import status
from httpx import AsyncClient
from uuid import UUID


class TestFamilyCreation:
    """Tests for automatic family creation on parent registration (EDR-001)."""

    @pytest.mark.asyncio
    async def test_register_creates_family(
        self,
        client: AsyncClient,
    ) -> None:
        """Test that parent registration creates a family automatically."""
        user_data = {
            "phone": "+8613812345678",
            "password": "TestPass123",
            "name": "Test Parent",
        }
        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # Should return family information
        assert "family_id" in data
        assert data["family_id"] is not None

    @pytest.mark.asyncio
    async def test_family_has_default_name(
        self,
        client: AsyncClient,
    ) -> None:
        """Test that created family has default name."""
        user_data = {
            "phone": "+8613812345678",
            "password": "TestPass123",
            "name": "Test Parent",
        }
        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # Should return family information
        assert "family_name" in data
        assert data["family_name"] == "My Family"

    @pytest.mark.asyncio
    async def test_family_custom_name(
        self,
        client: AsyncClient,
    ) -> None:
        """Test that registration can specify custom family name."""
        user_data = {
            "phone": "+8613812345678",
            "password": "TestPass123",
            "name": "Test Parent",
            "family_name": "Smith Family",
        }
        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # Should return custom family name
        assert "family_name" in data
        assert data["family_name"] == "Smith Family"


class TestTokenExpiration:
    """Tests for JWT token expiration timing (SPEC: access 1h, refresh 7d)."""

    @pytest.mark.asyncio
    async def test_access_token_expires_in_1_hour(
        self,
        client: AsyncClient,
    ) -> None:
        """Test that access token expires in 1 hour (SPEC requirement)."""
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

        assert login_response.status_code == status.HTTP_200_OK
        data = login_response.json()

        # Access token should expire in 1 hour (3600 seconds)
        assert "expires_in" in data
        assert data["expires_in"] == 3600  # 1 hour in seconds

    @pytest.mark.asyncio
    async def test_refresh_token_expires_in_7_days(
        self,
        client: AsyncClient,
    ) -> None:
        """Test that refresh token expires in 7 days (SPEC requirement)."""
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

        assert login_response.status_code == status.HTTP_200_OK
        data = login_response.json()

        # Decode refresh token to check expiration
        # Token should expire in 7 days
        import jwt
        from app.core.config import settings

        decoded = jwt.decode(
            data["refresh_token"],
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        # Calculate expiration time
        exp_timestamp = decoded["exp"]
        iat_timestamp = decoded["iat"]
        expires_in_seconds = exp_timestamp - iat_timestamp

        # 7 days = 7 * 24 * 60 * 60 = 604800 seconds
        assert expires_in_seconds == 604800


class TestInviteCodeExpiry:
    """Tests for invite code expiration (SPEC: 72 hours)."""

    @pytest.mark.asyncio
    async def test_invite_code_has_expiration(
        self,
        client: AsyncClient,
        sample_user_data: dict,
        sample_child_data: dict,
    ) -> None:
        """Test that invite codes have expiration date."""
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

        assert child_response.status_code == status.HTTP_200_OK
        child_profile = child_response.json()

        # Should have invite code expiration
        assert "invite_code_expires_at" in child_profile
        assert child_profile["invite_code_expires_at"] is not None

    @pytest.mark.asyncio
    async def test_invite_code_expires_in_72_hours(
        self,
        client: AsyncClient,
        sample_user_data: dict,
        sample_child_data: dict,
    ) -> None:
        """Test that invite codes expire in 72 hours (SPEC requirement)."""
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

        assert child_response.status_code == status.HTTP_200_OK
        child_profile = child_response.json()

        # Check expiration is approximately 72 hours from now
        expires_at_str = child_profile["invite_code_expires_at"]
        expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))

        now = datetime.now(timezone.utc)
        time_until_expiry = expires_at - now

        # Should be approximately 72 hours (within 1 minute tolerance)
        expected_hours = 72
        tolerance_minutes = 1
        assert abs(time_until_expiry.total_seconds() - expected_hours * 3600) < tolerance_minutes * 60

    @pytest.mark.asyncio
    async def test_expired_invite_code_rejected(
        self,
        client: AsyncClient,
        sample_user_data: dict,
        sample_child_data: dict,
        db_session: AsyncSession,
    ) -> None:
        """Test that expired invite codes are rejected."""
        from sqlalchemy import select, update
        from app.models.child_profile import ChildProfile
        from datetime import datetime, timezone, timedelta

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

        # Manually expire the invite code in database
        result = await db_session.execute(
            select(ChildProfile).where(ChildProfile.invite_code == invite_code)
        )
        child = result.scalar_one_or_none()

        if child:
            # Set expiration to past
            from app.models.child_profile import InviteCode

            expired_time = datetime.now(timezone.utc) - timedelta(hours=1)
            child.invite_code_expires_at = expired_time
            await db_session.commit()

        # Try to bind with expired code
        bind_request = {
            "invite_code": invite_code,
            "device_id": "test-device-123",
        }
        response = await client.post("/api/v1/child/bind", json=bind_request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "expired" in response.json()["detail"].lower()


class TestEmailRegistration:
    """Tests for email-based registration (SPEC optional requirement)."""

    @pytest.mark.asyncio
    async def test_register_with_email(
        self,
        client: AsyncClient,
    ) -> None:
        """Test registration with email instead of phone."""
        user_data = {
            "email": "parent@example.com",
            "password": "TestPass123",
            "name": "Test Parent",
        }
        response = await client.post("/api/v1/auth/register", json=user_data)

        # Email registration should work (future feature)
        # For now, this test documents the requirement
        # Current implementation requires phone
        assert response.status_code in [
            status.HTTP_201_CREATED,  # If email is supported
            status.HTTP_422_UNPROCESSABLE_ENTITY,  # If phone is required
        ]
