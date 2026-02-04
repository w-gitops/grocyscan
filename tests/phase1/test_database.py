"""Phase 1 database tests: homebot schema, tenants, users, tenant_memberships, RLS, Alembic."""

import os
import subprocess
import sys

import pytest

# Skip if not using PostgreSQL with homebot database
DATABASE_URL = os.environ.get("DATABASE_URL", "")
SKIP = "postgresql" not in DATABASE_URL or "homebot" not in DATABASE_URL


@pytest.mark.skipif(SKIP, reason="Requires PostgreSQL with DATABASE_URL containing homebot")
@pytest.mark.asyncio
async def test_current_database_returns_homebot():
    """[1] PostgreSQL database created with homebot schema - current_database() is homebot."""
    try:
        import asyncpg
    except ImportError:
        pytest.skip("asyncpg not installed")
    url = DATABASE_URL.replace("+asyncpg", "").replace("postgresql+asyncpg", "postgresql")
    conn = await asyncpg.connect(url)
    try:
        row = await conn.fetchrow("SELECT current_database() AS db")
        assert row is not None and row["db"] == "homebot"
    finally:
        await conn.close()


@pytest.mark.skipif(SKIP, reason="Requires PostgreSQL with homebot")
@pytest.mark.asyncio
async def test_tenants_table_and_rls():
    """[2] Tenants table with RLS enabled - columns id, name, slug, settings and RLS policy exists."""
    try:
        import asyncpg
    except ImportError:
        pytest.skip("asyncpg not installed")
    url = DATABASE_URL.replace("+asyncpg", "").replace("postgresql+asyncpg", "postgresql")
    conn = await asyncpg.connect(url)
    try:
        rows = await conn.fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='homebot' AND table_name='tenants' ORDER BY ordinal_position"
        )
        names = {r["column_name"] for r in rows}
        assert "id" in names and "name" in names and "slug" in names and "settings" in names
        policy = await conn.fetchval(
            "SELECT 1 FROM pg_policies WHERE schemaname='homebot' AND tablename='tenants' LIMIT 1"
        )
        assert policy is not None
    finally:
        await conn.close()


@pytest.mark.skipif(SKIP, reason="Requires PostgreSQL with homebot")
@pytest.mark.asyncio
async def test_users_and_tenant_memberships():
    """[3] Users table with tenant_id; tenant_memberships with user_id, tenant_id, role."""
    try:
        import asyncpg
    except ImportError:
        pytest.skip("asyncpg not installed")
    url = DATABASE_URL.replace("+asyncpg", "").replace("postgresql+asyncpg", "postgresql")
    conn = await asyncpg.connect(url)
    try:
        rows = await conn.fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='homebot' AND table_name='users' ORDER BY ordinal_position"
        )
        names = {r["column_name"] for r in rows}
        assert "id" in names and "email" in names and "password_hash" in names and "tenant_id" in names
        rows2 = await conn.fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='homebot' AND table_name='tenant_memberships' ORDER BY ordinal_position"
        )
        names2 = {r["column_name"] for r in rows2}
        assert "user_id" in names2 and "tenant_id" in names2 and "role" in names2
    finally:
        await conn.close()


def test_alembic_migrations_configured():
    """[4] Alembic migrations configured - alembic history shows revision chain."""
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "history"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, (result.stdout or "") + (result.stderr or "")
    # Should have at least 0001 and 0002 (initial + homebot schema)
    out = (result.stdout or "") + (result.stderr or "")
    assert "0001" in out or "0002" in out or "initial" in out.lower() or "homebot" in out.lower()
