"""Pytest configuration and fixtures for BabyEco backend tests."""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app

# Import models to register them with SQLAlchemy
from app.models.user import User  # noqa: F401
from app.models.child_profile import ChildProfile  # noqa: F401

# Test database URL (in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    from httpx import ASGITransport, AsyncClient

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data() -> dict[str, Any]:
    """Sample user registration data."""
    return {
        "phone_number": "13800138000",
        "nickname": "TestParent",
        "password": "SecurePass123!",
        "avatar": "https://example.com/avatar.png",
    }


@pytest.fixture
def sample_child_data() -> dict[str, Any]:
    """Sample child profile data."""
    return {
        "child_name": "TestChild",
        "child_age": 8,
        "child_avatar": "https://example.com/child_avatar.png",
    }
