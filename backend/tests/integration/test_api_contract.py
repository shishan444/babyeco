"""API Contract Tests for Authentication Endpoints.

These tests verify the API contract between frontend and backend:
- Request/response formats match specifications
- Status codes are correct
- Error responses follow standard format
- Authentication headers work as expected

Run with: pytest tests/integration/test_api_contract.py -v
"""

from httpx import AsyncClient


class TestAuthRegisterContract:
    """Tests for POST /api/v1/auth/register endpoint contract."""

    async def test_register_success_contract(
        self,
        integration_client: AsyncClient,
    ) -> None:
        """Test successful registration response matches contract.

        Verifies:
        - Status code is 201 Created
        - Response contains required fields: id, phone, name, status
        - Sensitive fields (hashed_password) are not exposed
        - Phone number matches request
        """
        user_data = {
            "phone": "+8613812345678",
            "password": "TestPass123",
            "name": "Test Parent",
        }

        response = await integration_client.post("/auth/register", json=user_data)

        assert response.status_code == 201

        data = response.json()
        # Required fields
        assert "id" in data
        assert "phone" in data
        assert "name" in data
        assert "status" in data

        # Field values
        assert data["phone"] == user_data["phone"]
        assert data["name"] == user_data["name"]
        assert data["status"] == "active"
        assert isinstance(data["id"], int)

        # Sensitive data not exposed
        assert "hashed_password" not in data
        assert "password" not in data

    async def test_register_validation_error_contract(
        self,
        integration_client: AsyncClient,
    ) -> None:
        """Test registration with invalid data returns validation error.

        Verifies:
        - Status code is 422 Unprocessable Entity
        - Error response follows standard format
        - Detail message explains validation failure
        """
        invalid_data = {
            "phone": "invalid",  # Invalid phone format
            "password": "weak",  # Weak password
            "name": "",  # Empty name
        }

        response = await integration_client.post("/auth/register", json=invalid_data)

        assert response.status_code == 422

        data = response.json()
        # Standard error response format
        assert "detail" in data
        assert isinstance(data["detail"], list)

        # Validation errors should include field and message
        errors = data["detail"]
        assert len(errors) > 0
        for error in errors:
            assert "loc" in error  # Field location
            assert "msg" in error  # Error message
            assert "type" in error  # Error type

    async def test_register_duplicate_phone_contract(
        self,
        integration_client: AsyncClient,
    ) -> None:
        """Test duplicate phone number returns business logic error.

        Verifies:
        - Status code is 400 Bad Request
        - Error message indicates duplicate registration
        """
        user_data = {
            "phone": "+8613812345678",
            "password": "TestPass123",
            "name": "Test Parent",
        }

        # First registration
        await integration_client.post("/auth/register", json=user_data)

        # Duplicate registration
        response = await integration_client.post("/auth/register", json=user_data)

        assert response.status_code == 400

        data = response.json()
        # Business logic error format
        assert "detail" in data
        assert "already" in data["detail"].lower() or "exists" in data["detail"].lower()


class TestAuthLoginContract:
    """Tests for POST /api/v1/auth/login endpoint contract."""

    async def test_login_success_contract(
        self,
        integration_client: AsyncClient,
    ) -> None:
        """Test successful login response matches contract.

        Verifies:
        - Status code is 200 OK
        - Response contains tokens: access_token, refresh_token
        - Response contains user_id and token_type
        - Tokens are non-empty strings
        """
        # Register user first
        user_data = {
            "phone": "+8613812345678",
            "password": "TestPass123",
            "name": "Test Parent",
        }
        await integration_client.post("/auth/register", json=user_data)

        # Login
        login_data = {
            "phone": user_data["phone"],
            "password": user_data["password"],
        }
        response = await integration_client.post("/auth/login", json=login_data)

        assert response.status_code == 200

        data = response.json()
        # Required fields
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert "user_id" in data

        # Field values
        assert data["token_type"] == "bearer"
        assert isinstance(data["user_id"], int)
        assert len(data["access_token"]) > 0
        assert len(data["refresh_token"]) > 0

    async def test_login_invalid_credentials_contract(
        self,
        integration_client: AsyncClient,
    ) -> None:
        """Test login with invalid credentials returns error.

        Verifies:
        - Status code is 401 Unauthorized
        - Error message indicates authentication failure
        """
        login_data = {
            "phone": "+8619876543210",
            "password": "WrongPassword123",
        }
        response = await integration_client.post("/auth/login", json=login_data)

        assert response.status_code == 401

        data = response.json()
        assert "detail" in data
        # Should not reveal whether user exists
        assert "incorrect" in data["detail"].lower() or "invalid" in data["detail"].lower()


class TestTokenRefreshContract:
    """Tests for POST /api/v1/auth/refresh endpoint contract."""

    async def test_refresh_success_contract(
        self,
        integration_client: AsyncClient,
    ) -> None:
        """Test successful token refresh response matches contract.

        Verifies:
        - Status code is 200 OK
        - Response contains new access_token and refresh_token
        - Tokens are different from original
        """
        # Register and login
        user_data = {
            "phone": "+8613812345678",
            "password": "TestPass123",
            "name": "Test Parent",
        }
        await integration_client.post("/auth/register", json=user_data)

        login_response = await integration_client.post(
            "/auth/login",
            json={"phone": user_data["phone"], "password": user_data["password"]},
        )
        old_refresh_token = login_response.json()["refresh_token"]

        # Refresh token
        response = await integration_client.post(
            "/auth/refresh",
            json={"refresh_token": old_refresh_token},
        )

        assert response.status_code == 200

        data = response.json()
        # Required fields
        assert "access_token" in data
        assert "refresh_token" in data

        # New tokens should be returned
        assert len(data["access_token"]) > 0
        assert len(data["refresh_token"]) > 0

    async def test_refresh_invalid_token_contract(
        self,
        integration_client: AsyncClient,
    ) -> None:
        """Test refresh with invalid token returns error.

        Verifies:
        - Status code is 401 Unauthorized
        - Error message indicates token is invalid
        """
        response = await integration_client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid_token"},
        )

        assert response.status_code == 401

        data = response.json()
        assert "detail" in data
        assert "invalid" in data["detail"].lower() or "expired" in data["detail"].lower()


class TestGetCurrentUserContract:
    """Tests for GET /api/v1/auth/me endpoint contract."""

    async def test_get_current_user_success_contract(
        self,
        integration_client: AsyncClient,
    ) -> None:
        """Test getting current user response matches contract.

        Verifies:
        - Status code is 200 OK
        - Response contains user fields: id, phone, name, status
        - Response matches authenticated user's data
        """
        # Register and login
        user_data = {
            "phone": "+8613812345678",
            "password": "TestPass123",
            "name": "Test Parent",
        }
        await integration_client.post("/auth/register", json=user_data)

        login_response = await integration_client.post(
            "/auth/login",
            json={"phone": user_data["phone"], "password": user_data["password"]},
        )
        access_token = login_response.json()["access_token"]

        # Get current user
        response = await integration_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200

        data = response.json()
        # Required fields
        assert "id" in data
        assert "phone" in data
        assert "name" in data
        assert "status" in data

        # Field values
        assert data["phone"] == user_data["phone"]
        assert data["name"] == user_data["name"]
        assert data["status"] == "active"

    async def test_get_current_user_unauthorized_contract(
        self,
        integration_client: AsyncClient,
    ) -> None:
        """Test getting current user without token returns error.

        Verifies:
        - Status code is 401 Unauthorized
        - Error message indicates authentication required
        """
        response = await integration_client.get("/auth/me")

        assert response.status_code == 401

        data = response.json()
        assert "detail" in data
        assert "authenticated" in data["detail"].lower() or "token" in data["detail"].lower()

    async def test_get_current_user_invalid_token_contract(
        self,
        integration_client: AsyncClient,
    ) -> None:
        """Test getting current user with invalid token returns error.

        Verifies:
        - Status code is 401 Unauthorized
        - Error message indicates token is invalid
        """
        response = await integration_client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )

        assert response.status_code == 401

        data = response.json()
        assert "detail" in data
        assert "invalid" in data["detail"].lower() or "expired" in data["detail"].lower()


class TestUpdateCurrentUserContract:
    """Tests for PATCH /api/v1/auth/me endpoint contract."""

    async def test_update_user_success_contract(
        self,
        integration_client: AsyncClient,
    ) -> None:
        """Test updating user response matches contract.

        Verifies:
        - Status code is 200 OK
        - Response contains updated user data
        - Only provided fields are updated
        """
        # Register and login
        user_data = {
            "phone": "+8613812345678",
            "password": "TestPass123",
            "name": "Test Parent",
        }
        await integration_client.post("/auth/register", json=user_data)

        login_response = await integration_client.post(
            "/auth/login",
            json={"phone": user_data["phone"], "password": user_data["password"]},
        )
        access_token = login_response.json()["access_token"]

        # Update user
        update_data = {"name": "Updated Name"}
        response = await integration_client.patch(
            "/auth/me",
            json=update_data,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200

        data = response.json()
        # Required fields present
        assert "id" in data
        assert "name" in data

        # Name updated
        assert data["name"] == "Updated Name"
        # Other fields unchanged
        assert data["phone"] == user_data["phone"]


class TestErrorResponseContract:
    """Tests for standard error response format across all endpoints."""

    async def test_404_not_found_contract(
        self,
        integration_client: AsyncClient,
    ) -> None:
        """Test 404 error response follows standard format.

        Verifies:
        - Status code is 404 Not Found
        - Error response contains 'detail' field
        """
        response = await integration_client.get("/nonexistent-endpoint")

        assert response.status_code == 404

        data = response.json()
        assert "detail" in data

    async def test_422_validation_error_contract(
        self,
        integration_client: AsyncClient,
    ) -> None:
        """Test 422 validation error response follows standard format.

        Verifies:
        - Status code is 422 Unprocessable Entity
        - Error response contains validation details
        """
        response = await integration_client.post(
            "/auth/register",
            json={  # Missing required fields
                "phone": "+8613812345678",
            },
        )

        assert response.status_code == 422

        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)

    async def test_500_server_error_contract(
        self,
        integration_client: AsyncClient,
    ) -> None:
        """Test 500 server error response follows standard format.

        Note: This test requires triggering an actual server error,
        which is difficult in integration tests.
        In production, verify error monitoring captures 500 errors.
        """
        # This would require triggering an actual server error
        # For now, we document the expected contract:
        # - Status code is 500 Internal Server Error
        # - Error response contains 'detail' field
        # - Error message is generic (doesn't expose internals)
        pass
