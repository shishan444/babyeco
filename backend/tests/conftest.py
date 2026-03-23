"""Test configuration and fixtures."""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from typing import Type
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

# Set test environment variables BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.middleware.rate_limit import _rate_limiter
from app.core.database import Base, get_db
from app.main import create_application

# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter state between tests.

    @MX:NOTE
    This fixture is automatically applied to all tests.
    It ensures rate limiting state doesn't leak between tests.
    """
    _rate_limiter.reset()
    yield
    _rate_limiter.reset()


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session() as session:
        yield session


@pytest.fixture
def app(db_session: AsyncSession) -> FastAPI:
    """Create test application with overridden dependencies."""
    app = create_application()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture
def sync_client(app: FastAPI) -> TestClient:
    """Create synchronous test client."""
    return TestClient(app)


@pytest.fixture
def sample_user_data() -> dict:
    """Sample user registration data with phone number."""
    return {
        "phone": "+8613812345678",
        "password": "TestPass123",
        "name": "Test Parent",
        "email": None,
    }


@pytest.fixture
def sample_child_data() -> dict:
    """Sample child profile data."""
    return {
        "name": "Test Child",
        "birth_date": "2016-01-15",
    }


@pytest.fixture
async def sample_child(db_session: AsyncSession, test_user):
    """Create sample child profile for testing."""
    from app.models.child_profile import ChildProfile
    from uuid import uuid4

    child = ChildProfile(
        id=uuid4(),
        parent_id=test_user.id,
        name="Test Child",
        points_balance=0,
        total_points_earned=0,
        current_streak=0,
        longest_streak=0,
    )
    db_session.add(child)
    await db_session.commit()
    await db_session.refresh(child)

    return child
