"""Test helper utilities for integration testing.

This module provides helper functions for:
- Creating test clients with custom configurations
- Setting up test data efficiently
- Cleaning up test data between tests
- Authentication helpers for various user types

All helpers are designed to minimize test boilerplate and ensure consistency.
"""

from collections.abc import AsyncGenerator, Mapping
from typing import Any
from uuid import uuid4

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token
from app.models.user import User


class ClientHelper:
    """Helper class for creating configured test clients.

    @MX:NOTE Static utility class for test client creation
    Provides pre-configured clients for common testing scenarios
    """

    @staticmethod
    async def create_client(
        app,
        base_url: str = "http://test/api/v1",
        headers: dict[str, str] | None = None,
    ) -> AsyncGenerator[AsyncClient, None]:
        """Create an async test client with custom configuration.

        @MX:ANCHOR Client creation helper
        @MX:REASON Centralizes client creation logic for consistent test setup

        Args:
            app: FastAPI application instance
            base_url: Base URL for all requests
            headers: Default headers to include with all requests

        Yields:
            Configured AsyncClient instance

        Example:
            async with ClientHelper.create_client(app) as client:
                response = await client.get("/users")
        """
        client = AsyncClient(
            transport=ASGITransport(app=app),
            base_url=base_url,
        )

        if headers:
            client.headers.update(headers)

        yield client

        await client.aclose()

    @staticmethod
    async def create_authenticated_client(
        app,
        user_id: int,
        base_url: str = "http://test/api/v1",
    ) -> AsyncGenerator[AsyncClient, None]:
        """Create a test client with pre-configured authentication.

        @MX:NOTE Client with JWT token already set in Authorization header
        Useful for tests that require authenticated user without registration

        Args:
            app: FastAPI application instance
            user_id: User ID to create token for
            base_url: Base URL for all requests

        Yields:
            Authenticated AsyncClient instance

        Example:
            async with ClientHelper.create_authenticated_client(app, user_id=1) as client:
                response = await client.get("/auth/me")
        """
        # Create tokens for user
        access_token = create_access_token(data={"sub": str(user_id)})
        refresh_token = create_refresh_token(data={"sub": str(user_id)})

        headers = {"Authorization": f"Bearer {access_token}"}

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url=base_url,
            headers=headers,
        ) as client:
            yield client


class DataHelper:
    """Helper class for efficient test data setup.

    @MX:NOTE Static utility class for test data management
    Provides methods for creating related entities efficiently
    """

    @staticmethod
    async def create_user_with_children(
        db: AsyncSession,
        num_children: int = 2,
        phone: str | None = None,
    ) -> User:
        """Create a user with multiple child profiles.

        @MX:NOTE Convenience method for creating complete family unit
        Reduces boilerplate in tests that need parent + children

        Args:
            db: Database session
            num_children: Number of child profiles to create
            phone: Phone number (auto-generated if None)

        Returns:
            Created User instance with children attached

        Example:
            parent = await DataHelper.create_user_with_children(db, num_children=3)
            assert len(parent.children) == 3
        """
        from tests.integration.fixtures import ChildFixtures, UserFixtures

        # Create parent
        parent = await UserFixtures.create_parent(db=db, phone=phone)

        # Create children
        for i in range(num_children):
            await ChildFixtures.create_child(
                db=db,
                parent_id=parent.id,
                name=f"Child {i + 1}",
            )

        # Refresh to load relationships
        await db.refresh(parent)

        return parent

    @staticmethod
    async def create_task_with_completion(
        db: AsyncSession,
        child_id: int,
        verified_by: int,
        points: int = 10,
    ) -> tuple:
        """Create a task with completion record.

        @MX:NOTE Convenience method for creating completed task
        Useful for testing points earning and task history

        Args:
            db: Database session
            child_id: Child profile ID
            verified_by: Parent user ID
            points: Points awarded for task

        Returns:
            Tuple of (Task, TaskCompletion)

        Example:
            task, completion = await DataHelper.create_task_with_completion(
                db, child_id=1, verified_by=1
            )
            assert task.status == "completed"
        """
        from tests.integration.fixtures import TaskFixtures

        task = await TaskFixtures.create_task(
            db=db,
            child_id=child_id,
            points=points,
        )

        completion = await TaskFixtures.create_completed_task(
            db=db,
            task=task,
            verified_by=verified_by,
        )

        return task, completion


class AuthHelper:
    """Helper class for authentication-related operations.

    @MX:NOTE Static utility class for authentication helpers
    Provides token creation and user authentication utilities
    """

    @staticmethod
    def create_auth_headers(user_id: int) -> dict[str, str]:
        """Create authentication headers for a user.

        @MX:ANCHOR Auth header creation helper
        @MX:REASON Centralizes token creation for consistent auth testing

        Args:
            user_id: User ID to create token for

        Returns:
            Dictionary with Authorization header

        Example:
            headers = AuthHelper.create_auth_headers(user_id=1)
            response = await client.get("/auth/me", headers=headers)
        """
        access_token = create_access_token(data={"sub": str(user_id)})
        return {"Authorization": f"Bearer {access_token}"}

    @staticmethod
    def create_auth_tokens(user_id: int) -> dict[str, str]:
        """Create access and refresh tokens for a user.

        Args:
            user_id: User ID to create tokens for

        Returns:
            Dictionary with access_token and refresh_token

        Example:
            tokens = AuthHelper.create_auth_tokens(user_id=1)
            access_token = tokens["access_token"]
            refresh_token = tokens["refresh_token"]
        """
        return {
            "access_token": create_access_token(data={"sub": str(user_id)}),
            "refresh_token": create_refresh_token(data={"sub": str(user_id)}),
        }

    @staticmethod
    async def register_and_login(
        client: AsyncClient,
        phone: str | None = None,
        password: str = "TestPass123",
        name: str = "Test User",
    ) -> tuple[dict[str, Any], str]:
        """Register a new user and log them in.

        @MX:NOTE Convenience method for user registration + login
        Returns user data and access token

        Args:
            client: HTTP client
            phone: Phone number (auto-generated if None)
            password: User password
            name: User display name

        Returns:
            Tuple of (user_data, access_token)

        Example:
            user_data, token = await AuthHelper.register_and_login(client)
            assert user_data["phone"] == "+8613812345678"
        """
        if phone is None:
            phone = f"+86138{uuid4().int % 100000000:08d}"

        # Register
        user_data = {
            "phone": phone,
            "password": password,
            "name": name,
        }
        await client.post("/auth/register", json=user_data)

        # Login
        login_response = await client.post(
            "/auth/login",
            json={"phone": phone, "password": password},
        )

        token_data = login_response.json()
        return user_data, token_data["access_token"]


class CleanupHelper:
    """Helper class for test data cleanup.

    @MX:NOTE Static utility class for cleanup operations
    Provides methods for cleaning up test data efficiently
    """

    @staticmethod
    async def truncate_tables(db: AsyncSession, *models: type) -> None:
        """Truncate database tables for clean test state.

        @MX:WARN This is a destructive operation
        @MX:REASON Only use when transaction rollback is not sufficient

        Args:
            db: Database session
            *models: Model classes to truncate

        Example:
            await CleanupHelper.truncate_tables(db, User, ChildProfile, Task)
        """
        for model in models:
            await db.execute(model.__table__.delete())
        await db.commit()

    @staticmethod
    async def delete_user_cascade(
        db: AsyncSession,
        user_id: int,
    ) -> None:
        """Delete user and all related data.

        @MX:NOTE Convenience method for cascading user deletion
        Removes user, children, tasks, and points transactions

        Args:
            db: Database session
            user_id: User ID to delete

        Example:
            await CleanupHelper.delete_user_cascade(db, user_id=1)
        """
        from app.models.child import ChildProfile
        from app.models.points import PointsTransaction
        from app.models.task import Task
        from app.models.user import User

        # Delete child-related data
        children = await db.execute(
            ChildProfile.__table__.select().where(ChildProfile.parent_id == user_id)
        )
        child_ids = [c.id for c in children]

        for child_id in child_ids:
            # Delete tasks and completions
            await db.execute(Task.__table__.delete().where(Task.child_id == child_id))
            # Delete points transactions
            await db.execute(
                PointsTransaction.__table__.delete().where(
                    PointsTransaction.child_id == child_id
                )
            )
            # Delete child
            await db.execute(
                ChildProfile.__table__.delete().where(ChildProfile.id == child_id)
            )

        # Delete user
        await db.execute(User.__table__.delete().where(User.id == user_id))

        await db.commit()


class AssertionHelper:
    """Helper class for common test assertions.

    @MX:NOTE Static utility class for reusable assertions
    Reduces test code duplication
    """

    @staticmethod
    def assert_user_response(
        data: Mapping[str, Any],
        expected_phone: str | None = None,
        expected_name: str | None = None,
    ) -> None:
        """Assert user response matches expected format.

        @MX:ANCHOR User response assertion helper
        @MX:REASON Ensures consistent user response validation across tests

        Args:
            data: Response data from API
            expected_phone: Expected phone number (optional)
            expected_name: Expected name (optional)

        Raises:
            AssertionError: If response doesn't match expected format
        """
        # Required fields
        assert "id" in data
        assert "phone" in data
        assert "name" in data
        assert "status" in data

        # Field types
        assert isinstance(data["id"], int)
        assert isinstance(data["phone"], str)
        assert isinstance(data["name"], str)
        assert isinstance(data["status"], str)

        # Expected values
        if expected_phone:
            assert data["phone"] == expected_phone
        if expected_name:
            assert data["name"] == expected_name

        # No sensitive data
        assert "hashed_password" not in data
        assert "password" not in data

    @staticmethod
    def assert_error_response(
        data: Mapping[str, Any],
        expected_status: int,
        expected_detail_contains: str | None = None,
    ) -> None:
        """Assert error response matches expected format.

        @MX:ANCHOR Error response assertion helper
        @MX:REASON Ensures consistent error response validation

        Args:
            data: Response data from API
            expected_status: Expected HTTP status code
            expected_detail_contains: Expected substring in error detail

        Raises:
            AssertionError: If response doesn't match expected format
        """
        assert "detail" in data

        if expected_detail_contains:
            assert expected_detail_contains.lower() in data["detail"].lower()

    @staticmethod
    def assert_pagination_response(
        data: Mapping[str, Any],
        min_items: int = 0,
        max_items: int | None = None,
    ) -> None:
        """Assert paginated response matches expected format.

        Args:
            data: Response data from API
            min_items: Minimum expected items
            max_items: Maximum expected items (optional)

        Raises:
            AssertionError: If response doesn't match expected format
        """
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data

        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["page"], int)
        assert isinstance(data["size"], int)

        assert len(data["items"]) >= min_items
        if max_items is not None:
            assert len(data["items"]) <= max_items
