"""Pytest fixtures and configuration."""

import contextlib
import os
import tempfile
import time
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

TEST_DATABASE_URL = os.environ.get("DATABASE_URL", "")
USE_POSTGRES = "postgresql" in TEST_DATABASE_URL
if os.environ.get("CI", "").lower() == "true" and not USE_POSTGRES:
    raise RuntimeError("CI requires PostgreSQL DATABASE_URL for tests.")
if not USE_POSTGRES:
    TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
else:
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# Ensure app settings pick up test env before import.
os.environ.setdefault("AUTH_ENABLED", "false")

from app.config import Settings
from app.db.database import Base, get_db
from app.main import app

ROOT_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session", autouse=True)
def isolate_settings_file(tmp_path_factory) -> None:
    """Use a temp settings file to avoid cross-test leakage."""
    from app.services.settings import settings_service

    settings_service.SETTINGS_FILE = str(
        tmp_path_factory.mktemp("settings") / "settings.json"
    )
    settings_service._settings = None
    settings_service._test_settings_file = settings_service.SETTINGS_FILE


@pytest.fixture(autouse=True)
def reset_settings_cache() -> None:
    """Reset settings cache and file between tests."""
    import os

    from app.services.settings import settings_service

    settings_service.SETTINGS_FILE = getattr(
        settings_service, "_test_settings_file", settings_service.SETTINGS_FILE
    )
    settings_service._settings = None
    if settings_service.SETTINGS_FILE and os.path.exists(settings_service.SETTINGS_FILE):
        os.remove(settings_service.SETTINGS_FILE)


@pytest.hookimpl(tryfirst=True)
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Fail CI runs if any tests were skipped."""
    if os.environ.get("CI", "").lower() != "true":
        return
    if session.testsfailed:
        return
    skipped = len(getattr(session, "skipped", [])) if hasattr(session, "skipped") else None
    if skipped is None:
        # Pytest doesn't store skipped counts by default; use stats dict.
        skipped = len(session.stats.get("skipped", [])) if hasattr(session, "stats") else 0
    if skipped:
        session.exitstatus = 1


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


@pytest.fixture(scope="session", autouse=True)
def migrate_database() -> Generator[None, None, None]:
    """Apply Alembic migrations for Postgres tests."""
    if not USE_POSTGRES:
        yield
        return
    worker_id = os.environ.get("PYTEST_XDIST_WORKER")

    @contextlib.contextmanager
    def _migration_lock() -> Generator[None, None, None]:
        lock_path = os.path.join(tempfile.gettempdir(), "alembic-migrate.lock")
        with open(lock_path, "w", encoding="utf-8") as lock_file:
            import fcntl

            fcntl.flock(lock_file, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file, fcntl.LOCK_UN)

    def _sync_database_url() -> str:
        return TEST_DATABASE_URL.replace("+asyncpg", "").replace("postgresql+asyncpg", "postgresql")

    def _at_head(config: Config) -> bool:
        head = ScriptDirectory.from_config(config).get_current_head()
        if not head:
            return True
        try:
            engine = create_engine(_sync_database_url())
            with engine.connect() as conn:
                version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
            return version == head
        except Exception:
            return False

    config = Config(str(ROOT_DIR / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)

    with _migration_lock():
        if not _at_head(config):
            command.upgrade(config, "head")
    # Wait for migrations if another worker applied them
    deadline = time.time() + 60
    while not _at_head(config):
        if time.time() > deadline:
            raise RuntimeError("Timed out waiting for Alembic migrations")
        time.sleep(1)
    yield
    if worker_id is None:
        with _migration_lock():
            command.downgrade(config, "base")


@pytest_asyncio.fixture(scope="session")
async def test_engine() -> AsyncGenerator[Any, None]:
    """Create test database engine.

    Yields:
        AsyncEngine: Test database engine
    """
    if USE_POSTGRES:
        engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        yield engine
        await engine.dispose()
        return

    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _attach_homebot(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("ATTACH DATABASE ':memory:' AS homebot")
        finally:
            cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine

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

    from app.config import settings as app_settings

    app.dependency_overrides[get_db] = override_get_db
    previous_env = app_settings.grocyscan_env
    previous_auth_enabled = app_settings.auth_enabled
    app_settings.grocyscan_env = "production"
    app_settings.auth_enabled = False
    with TestClient(app) as c:
        yield c
    app_settings.grocyscan_env = previous_env
    app_settings.auth_enabled = previous_auth_enabled
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
