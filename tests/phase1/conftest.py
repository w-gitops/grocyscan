"""Phase 1 test fixtures."""

import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app

# Skip database schema tests unless running against PostgreSQL with homebot schema
DATABASE_URL = os.environ.get("DATABASE_URL", "")
SKIP_DB_TESTS = "postgresql" not in DATABASE_URL or "homebot" not in DATABASE_URL


def requires_homebot_db(reason: str = "Requires PostgreSQL with DATABASE_URL containing homebot"):
    """Decorator to skip test when homebot DB is not configured."""
    return pytest.mark.skipif(SKIP_DB_TESTS, reason=reason)


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for Phase 1 API tests."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
