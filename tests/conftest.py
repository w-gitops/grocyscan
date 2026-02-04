"""Pytest fixtures and configuration."""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure tests always use PostgreSQL (never SQLite).
TEST_DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not TEST_DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be set to a PostgreSQL database for tests.")
if "postgresql" not in TEST_DATABASE_URL:
    raise RuntimeError("DATABASE_URL must use PostgreSQL (postgresql+asyncpg).")

# Ensure app settings pick up DATABASE_URL before import.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from app.config import Settings
from app.db.database import Base, get_db
from app.main import app


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session.

    Yields:
        asyncio.AbstractEventLoop: Event loop instance
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Create test settings.

    Returns:
        Settings: Test configuration
    """
    return Settings(
        grocyscan_env="development",
        grocyscan_debug=True,
        database_url=TEST_DATABASE_URL,  # type: ignore
        auth_enabled=False,
        otel_enabled=False,
        log_format="console",
        log_level="DEBUG",
    )


@pytest_asyncio.fixture(scope="session")
async def test_engine() -> AsyncGenerator[Any, None]:
    """Create test database engine.

    Yields:
        AsyncEngine: Test database engine
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS homebot"))
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(text("DROP SCHEMA IF EXISTS homebot CASCADE"))

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: Any) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session with automatic rollback.

    Args:
        test_engine: Test database engine

    Yields:
        AsyncSession: Database session that rolls back after test
    """
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
def client(db_session: AsyncSession) -> Generator[TestClient, None, None]:
    """Create test client with database dependency override.

    Args:
        db_session: Test database session

    Yields:
        TestClient: FastAPI test client
    """

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client.

    Args:
        db_session: Test database session

    Yields:
        AsyncClient: Async HTTP client for testing
    """

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),  # type: ignore
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()
