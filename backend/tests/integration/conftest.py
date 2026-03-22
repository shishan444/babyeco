"""Integration test configuration with test database and client fixtures.

This module provides fixtures for integration testing including:
- Test database with automatic setup and teardown
- Test client factory for API testing
- Authentication helpers for creating authenticated users
- Cleanup utilities for test isolation
"""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.database import Base
from app.main import create_application

# Test database configuration
# @MX:NOTE Integration tests use PostgreSQL test database, not in-memory SQLite
# This ensures full compatibility with production database features
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/babyeco_test",
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests.

    @MX:ANCHOR Session-scoped event loop for all integration tests
    @MX:REASON Prevents event loop closure issues in long-running test suites
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine.

    @MX:NOTE Engine is session-scoped to avoid recreating database between tests
    Database tables are created once and cleaned between test functions
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,  # Disable pooling for tests
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after tests complete
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session with automatic cleanup.

    @MX:ANCHOR Database session fixture for integration tests
    @MX:REASON Provides clean database state for each test via transaction rollback

    This fixture:
    1. Creates a new session for each test
    2. Wraps test in a transaction
    3. Rolls back transaction after test (cleanup)
    4. Closes session to prevent connection leaks
    """
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session() as session:
        # Begin transaction for test isolation
        await session.begin()

        yield session

        # Rollback to clean up test data
        await session.rollback()


@pytest.fixture
def app(db_session: AsyncSession):
    """Create test application with database dependency override.

    @MX:NOTE Override dependency injection to use test database session
    This ensures all API calls use the test database, not production
    """
    from app.core.database import get_db

    app = create_application()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture
async def integration_client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client for integration testing.

    @MX:ANCHOR HTTP client for integration tests
    @MX:REASON Provides ASGI transport for testing FastAPI without HTTP server

    Usage:
        async def test_example(integration_client):
            response = await integration_client.get("/api/v1/users")
            assert response.status_code == 200
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test/api/v1",
    ) as client:
        yield client


@pytest.fixture
async def authenticated_client(integration_client: AsyncClient) -> AsyncGenerator[AsyncClient, None]:
    """Create authenticated test client with valid JWT token.

    @MX:NOTE Automatically registers and logs in a test user
    Returns client with Authorization header pre-configured

    Usage:
        async def test_protected_endpoint(authenticated_client):
            response = await authenticated_client.get("/auth/me")
            assert response.status_code == 200
    """
    # Register test user
    user_data = {
        "phone": f"+86138{uuid4().int % 100000000:08d}",
        "password": "TestPass123",
        "name": "Integration Test User",
    }
    await integration_client.post("/auth/register", json=user_data)

    # Login to get token
    login_response = await integration_client.post(
        "/auth/login",
        json={"phone": user_data["phone"], "password": user_data["password"]},
    )
    token_data = login_response.json()

    # Add token to client headers
    integration_client.headers.update(
        {"Authorization": f"Bearer {token_data['access_token']}"}
    )

    yield integration_client


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Generate dummy authorization headers for testing.

    @MX:NOTE Use this for tests that don't require actual authentication
    For tests needing valid auth, use authenticated_client fixture instead
    """
    return {"Authorization": "Bearer dummy_token_for_testing"}
