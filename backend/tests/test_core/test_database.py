"""Tests for database module.

RED Phase: These tests define the expected behavior for database connection.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base, get_db


class TestDatabaseEngine:
    """Test suite for database engine configuration."""

    def test_base_model_exists(self):
        """Base model should be defined for SQLAlchemy models."""
        assert Base is not None
        assert hasattr(Base, "metadata")

    def test_get_db_is_callable(self):
        """get_db should be an async generator function."""
        assert callable(get_db)
        import inspect
        assert inspect.isasyncgenfunction(get_db)


class TestDatabaseConnection:
    """Test database connection functionality."""

    @pytest.mark.asyncio
    async def test_database_creates_tables(self, test_engine):
        """Database should be able to create all tables."""
        from sqlalchemy import text

        async with test_engine.begin() as conn:
            # Check that we can query the database
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_database_session_works(self, db_session: AsyncSession):
        """Database session should be functional."""
        assert db_session is not None
        from sqlalchemy import text

        result = await db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_database_session_isolation(self, db_session: AsyncSession):
        """Each test should get an isolated database session."""
        from sqlalchemy import text

        # Create a temporary table
        await db_session.execute(
            text("CREATE TEMP TABLE test_isolation (id INTEGER)")
        )
        await db_session.commit()

        # Verify it exists
        result = await db_session.execute(
            text("SELECT name FROM sqlite_temp_master WHERE type='table'")
        )
        tables = [row[0] for row in result.fetchall()]
        assert "test_isolation" in tables


class TestDatabaseModels:
    """Test that database models are properly registered."""

    def test_base_metadata_has_tables(self):
        """Base metadata should register model tables."""
        # Tables will be registered when models are imported
        # This test will be meaningful after models are created
        assert hasattr(Base, "metadata")


class TestInitDB:
    """Test database initialization."""

    @pytest.mark.asyncio
    async def test_init_db_function(self):
        """Test init_db creates tables."""
        from sqlalchemy.ext.asyncio import create_async_engine

        # Create a temporary engine
        temp_engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
            future=True,
        )

        # Patch the engine in database module temporarily
        from app.core import database
        original_engine = database.engine
        database.engine = temp_engine

        try:
            await database.init_db()

            # Verify tables were created
            from sqlalchemy import text
            async with temp_engine.begin() as conn:
                result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                tables = [row[0] for row in result.fetchall()]
                assert "users" in tables
                assert "child_profiles" in tables
        finally:
            database.engine = original_engine
            await temp_engine.dispose()

    @pytest.mark.asyncio
    async def test_get_db_generator(self):
        """Test get_db generator yields session and closes properly."""
        from sqlalchemy.ext.asyncio import create_async_engine

        # Create a temporary engine
        temp_engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
            future=True,
        )

        # Patch the engine in database module temporarily
        from app.core import database
        original_engine = database.engine
        original_session_maker = database.async_session_maker
        database.engine = temp_engine
        database.async_session_maker = database.async_session_maker.__class__(temp_engine)

        try:
            # Use the generator
            gen = database.get_db()
            session = await gen.__anext__()
            assert session is not None
            # Consume the generator fully
            try:
                await gen.__anext__()
            except StopAsyncIteration:
                pass
        finally:
            database.engine = original_engine
            database.async_session_maker = original_session_maker
            await temp_engine.dispose()
