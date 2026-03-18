"""Tests for AuthService.

RED Phase: These tests define the expected behavior for authentication service.
"""

import pytest
from datetime import timedelta

from app.schemas.auth import UserRegisterRequest, UserLoginRequest
from app.services.auth_service import AuthService


class TestAuthService:
    """Test suite for AuthService."""

    def test_auth_service_exists(self):
        """AuthService should be importable."""
        assert AuthService is not None

    def test_auth_service_has_register(self):
        """AuthService should have register method."""
        service = AuthService(None, None)
        assert hasattr(service, "register")

    def test_auth_service_has_login(self):
        """AuthService should have login method."""
        service = AuthService(None, None)
        assert hasattr(service, "login")

    def test_auth_service_has_create_access_token(self):
        """AuthService should have create_access_token method."""
        service = AuthService(None, None)
        assert hasattr(service, "create_access_token")

    def test_auth_service_has_verify_token(self):
        """AuthService should have verify_token method."""
        service = AuthService(None, None)
        assert hasattr(service, "verify_token")


class TestAuthServiceRegister:
    """Test auth service register operation."""

    @pytest.mark.asyncio
    async def test_register_new_user(self, db_session):
        """Should register a new user successfully."""
        from app.repositories.user_repository import UserRepository

        user_repo = UserRepository(db_session)
        auth_service = AuthService(user_repo, None)

        request = UserRegisterRequest(
            phone_number="13700000001",
            nickname="NewUser",
            password="SecurePass123!",
        )

        user = await auth_service.register(request)

        assert user is not None
        assert user.phone_number == "13700000001"
        assert user.nickname == "NewUser"
        assert user.password_hash != "SecurePass123!"  # Should be hashed

    @pytest.mark.asyncio
    async def test_register_duplicate_phone_fails(self, db_session):
        """Should fail to register with duplicate phone number."""
        from app.repositories.user_repository import UserRepository

        user_repo = UserRepository(db_session)
        auth_service = AuthService(user_repo, None)

        request1 = UserRegisterRequest(
            phone_number="13700000002",
            nickname="User1",
            password="Password123!",
        )
        await auth_service.register(request1)

        request2 = UserRegisterRequest(
            phone_number="13700000002",  # Same phone number
            nickname="User2",
            password="Password456!",
        )

        with pytest.raises(Exception):  # Should raise error
            await auth_service.register(request2)

    @pytest.mark.asyncio
    async def test_register_with_avatar(self, db_session):
        """Should register user with optional avatar."""
        from app.repositories.user_repository import UserRepository

        user_repo = UserRepository(db_session)
        auth_service = AuthService(user_repo, None)

        request = UserRegisterRequest(
            phone_number="13700000003",
            nickname="AvatarUser",
            password="SecurePass123!",
            avatar="https://example.com/avatar.png",
        )

        user = await auth_service.register(request)

        assert user.avatar == "https://example.com/avatar.png"


class TestAuthServiceLogin:
    """Test auth service login operation."""

    @pytest.mark.asyncio
    async def test_login_success(self, db_session):
        """Should login successfully with correct credentials."""
        from app.repositories.user_repository import UserRepository

        user_repo = UserRepository(db_session)
        auth_service = AuthService(user_repo, None)

        # Register user first
        register_request = UserRegisterRequest(
            phone_number="13700000010",
            nickname="LoginUser",
            password="CorrectPassword!",
        )
        await auth_service.register(register_request)

        # Login
        login_request = UserLoginRequest(
            phone_number="13700000010",
            password="CorrectPassword!",
        )

        result = await auth_service.login(login_request)

        assert result is not None
        assert "access_token" in result
        assert "token_type" in result
        assert result["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password_fails(self, db_session):
        """Should fail login with wrong password."""
        from app.repositories.user_repository import UserRepository

        user_repo = UserRepository(db_session)
        auth_service = AuthService(user_repo, None)

        # Register user first
        register_request = UserRegisterRequest(
            phone_number="13700000011",
            nickname="WrongPassUser",
            password="CorrectPassword!",
        )
        await auth_service.register(register_request)

        # Login with wrong password
        login_request = UserLoginRequest(
            phone_number="13700000011",
            password="WrongPassword!",
        )

        with pytest.raises(Exception):  # Should raise error
            await auth_service.login(login_request)

    @pytest.mark.asyncio
    async def test_login_nonexistent_user_fails(self, db_session):
        """Should fail login with non-existent user."""
        from app.repositories.user_repository import UserRepository

        user_repo = UserRepository(db_session)
        auth_service = AuthService(user_repo, None)

        login_request = UserLoginRequest(
            phone_number="99999999999",
            password="AnyPassword!",
        )

        with pytest.raises(Exception):  # Should raise error
            await auth_service.login(login_request)


class TestAuthServiceToken:
    """Test auth service token operations."""

    @pytest.mark.asyncio
    async def test_create_access_token(self, db_session):
        """Should create valid access token."""
        from app.repositories.user_repository import UserRepository

        user_repo = UserRepository(db_session)
        auth_service = AuthService(user_repo, None)

        token = auth_service.create_access_token(subject="user123")

        assert token is not None
        assert isinstance(token, str)

    @pytest.mark.asyncio
    async def test_verify_valid_token(self, db_session):
        """Should verify valid token successfully."""
        from app.repositories.user_repository import UserRepository

        user_repo = UserRepository(db_session)
        auth_service = AuthService(user_repo, None)

        token = auth_service.create_access_token(subject="user456")
        payload = auth_service.verify_token(token)

        assert payload is not None
        assert payload["sub"] == "user456"

    @pytest.mark.asyncio
    async def test_verify_invalid_token(self, db_session):
        """Should return None for invalid token."""
        from app.repositories.user_repository import UserRepository

        user_repo = UserRepository(db_session)
        auth_service = AuthService(user_repo, None)

        payload = auth_service.verify_token("invalid.token.here")

        assert payload is None

    @pytest.mark.asyncio
    async def test_create_token_with_expiry(self, db_session):
        """Should create token with custom expiry."""
        from app.repositories.user_repository import UserRepository

        user_repo = UserRepository(db_session)
        auth_service = AuthService(user_repo, None)

        expires = timedelta(hours=2)
        token = auth_service.create_access_token(
            subject="user789",
            expires_delta=expires,
        )

        payload = auth_service.verify_token(token)
        assert payload is not None

    @pytest.mark.asyncio
    async def test_login_returns_user_info(self, db_session):
        """Should return user info along with token."""
        from app.repositories.user_repository import UserRepository

        user_repo = UserRepository(db_session)
        auth_service = AuthService(user_repo, None)

        # Register user first
        register_request = UserRegisterRequest(
            phone_number="13700000020",
            nickname="UserInfoUser",
            password="Password123!",
        )
        registered_user = await auth_service.register(register_request)

        # Login
        login_request = UserLoginRequest(
            phone_number="13700000020",
            password="Password123!",
        )

        result = await auth_service.login(login_request)

        assert "user" in result
        assert result["user"]["nickname"] == "UserInfoUser"
        assert result["user"]["phone_number"] == "13700000020"
