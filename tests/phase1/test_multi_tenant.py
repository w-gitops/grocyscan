"""Phase 1 multi-tenant tests: RLS isolation and service tokens."""
import os
import uuid

import pytest

DATABASE_URL = os.environ.get("DATABASE_URL", "")
SKIP = "postgresql" not in DATABASE_URL or "homebot" not in DATABASE_URL


async def _connect():
    try:
        import asyncpg
    except ImportError:  # pragma: no cover - optional dependency
        pytest.skip("asyncpg not installed")
    url = DATABASE_URL.replace("+asyncpg", "").replace("postgresql+asyncpg", "postgresql")
    conn = await asyncpg.connect(url)
    # Ensure RLS is enforced. Prefer app_user role when available.
    try:
        await conn.execute("SET ROLE app_user")
    except Exception:
        # Role may not exist or current user cannot SET ROLE.
        pass
    await conn.execute("SET row_security = on")
    return conn


async def _set_tenant(conn, tenant_id: uuid.UUID) -> None:
    await conn.execute("SELECT set_config('app.tenant_id', $1, true)", str(tenant_id))


async def _clear_tenant(conn) -> None:
    await conn.execute("SELECT set_config('app.tenant_id', '', true)")


async def _insert_tenant(conn, tenant_id: uuid.UUID, name: str) -> None:
    slug = f"{name.lower().replace(' ', '-')}-{str(tenant_id)[:8]}"
    await _set_tenant(conn, tenant_id)
    await conn.execute(
        """
        INSERT INTO homebot.tenants (id, name, slug, settings, created_at, updated_at)
        VALUES ($1, $2, $3, NULL, now(), now())
        """,
        tenant_id,
        name,
        slug,
    )


async def _insert_product(conn, tenant_id: uuid.UUID, name: str) -> uuid.UUID:
    product_id = uuid.uuid4()
    await _set_tenant(conn, tenant_id)
    await conn.execute(
        """
        INSERT INTO homebot.products (id, tenant_id, name, name_normalized, created_at, updated_at)
        VALUES ($1, $2, $3, $4, now(), now())
        """,
        product_id,
        tenant_id,
        name,
        name.lower(),
    )
    return product_id


async def _insert_service_account(conn, tenant_id: uuid.UUID, name: str) -> uuid.UUID:
    account_id = uuid.uuid4()
    await _set_tenant(conn, tenant_id)
    await conn.execute(
        """
        INSERT INTO homebot.service_accounts (id, tenant_id, name, created_at)
        VALUES ($1, $2, $3, now())
        """,
        account_id,
        tenant_id,
        name,
    )
    return account_id


async def _insert_service_token(conn, tenant_id: uuid.UUID, account_id: uuid.UUID) -> uuid.UUID:
    token_id = uuid.uuid4()
    await _set_tenant(conn, tenant_id)
    await conn.execute(
        """
        INSERT INTO homebot.service_tokens (id, service_account_id, token_hash, scopes, created_at)
        VALUES ($1, $2, $3, $4, now())
        """,
        token_id,
        account_id,
        "bcrypt$hash",
        ["inventory:read"],
    )
    return token_id


@pytest.mark.skipif(SKIP, reason="Requires PostgreSQL with DATABASE_URL containing homebot")
@pytest.mark.asyncio
async def test_two_tenants_can_share_product_name():
    """Two tenants can have products with the same name."""
    conn = await _connect()
    await conn.execute("BEGIN")
    try:
        tenant_a = uuid.uuid4()
        tenant_b = uuid.uuid4()
        await _insert_tenant(conn, tenant_a, "Tenant A")
        await _insert_tenant(conn, tenant_b, "Tenant B")

        name = "Milk"
        await _insert_product(conn, tenant_a, name)
        await _insert_product(conn, tenant_b, name)

        await _set_tenant(conn, tenant_a)
        count_a = await conn.fetchval("SELECT count(*) FROM homebot.products WHERE name = $1", name)
        await _set_tenant(conn, tenant_b)
        count_b = await conn.fetchval("SELECT count(*) FROM homebot.products WHERE name = $1", name)

        assert count_a == 1
        assert count_b == 1
    finally:
        await conn.execute("ROLLBACK")
        await conn.close()


@pytest.mark.skipif(SKIP, reason="Requires PostgreSQL with DATABASE_URL containing homebot")
@pytest.mark.asyncio
async def test_queries_without_tenant_context_fail():
    """Queries without tenant context return no rows (RLS enforced)."""
    conn = await _connect()
    await conn.execute("BEGIN")
    try:
        tenant_id = uuid.uuid4()
        await _insert_tenant(conn, tenant_id, "Tenant RLS")
        await _insert_product(conn, tenant_id, "Bread")

        await _clear_tenant(conn)
        try:
            count = await conn.fetchval("SELECT count(*) FROM homebot.products")
        except Exception:
            assert True
        else:
            assert count == 0
    finally:
        await conn.execute("ROLLBACK")
        await conn.close()


@pytest.mark.skipif(SKIP, reason="Requires PostgreSQL with DATABASE_URL containing homebot")
@pytest.mark.asyncio
async def test_token_in_tenant_a_cannot_resolve_tenant_b_objects():
    """Token tied to tenant A cannot be queried from tenant B context."""
    conn = await _connect()
    await conn.execute("BEGIN")
    try:
        tenant_a = uuid.uuid4()
        tenant_b = uuid.uuid4()
        await _insert_tenant(conn, tenant_a, "Tenant A")
        await _insert_tenant(conn, tenant_b, "Tenant B")

        account_a = await _insert_service_account(conn, tenant_a, "svc-a")
        token_a = await _insert_service_token(conn, tenant_a, account_a)

        await _set_tenant(conn, tenant_b)
        row = await conn.fetchrow(
            "SELECT id FROM homebot.service_tokens WHERE id = $1",
            token_a,
        )
        assert row is None
    finally:
        await conn.execute("ROLLBACK")
        await conn.close()


@pytest.mark.skipif(SKIP, reason="Requires PostgreSQL with DATABASE_URL containing homebot")
@pytest.mark.asyncio
async def test_service_token_is_restricted_to_its_tenant():
    """Service tokens are only visible within their tenant context."""
    conn = await _connect()
    await conn.execute("BEGIN")
    try:
        tenant_a = uuid.uuid4()
        tenant_b = uuid.uuid4()
        await _insert_tenant(conn, tenant_a, "Tenant A")
        await _insert_tenant(conn, tenant_b, "Tenant B")

        account_a = await _insert_service_account(conn, tenant_a, "svc-a")
        account_b = await _insert_service_account(conn, tenant_b, "svc-b")
        await _insert_service_token(conn, tenant_a, account_a)
        await _insert_service_token(conn, tenant_b, account_b)

        await _set_tenant(conn, tenant_a)
        count_a = await conn.fetchval("SELECT count(*) FROM homebot.service_tokens")
        await _set_tenant(conn, tenant_b)
        count_b = await conn.fetchval("SELECT count(*) FROM homebot.service_tokens")

        assert count_a == 1
        assert count_b == 1
    finally:
        await conn.execute("ROLLBACK")
        await conn.close()


@pytest.mark.skipif(SKIP, reason="Requires PostgreSQL with DATABASE_URL containing homebot")
@pytest.mark.asyncio
async def test_rls_prevents_cross_tenant_access():
    """RLS prevents tenant B from reading tenant A rows."""
    conn = await _connect()
    await conn.execute("BEGIN")
    try:
        tenant_a = uuid.uuid4()
        tenant_b = uuid.uuid4()
        await _insert_tenant(conn, tenant_a, "Tenant A")
        await _insert_tenant(conn, tenant_b, "Tenant B")

        product_id = await _insert_product(conn, tenant_a, "Apples")

        await _set_tenant(conn, tenant_b)
        row = await conn.fetchrow(
            "SELECT id FROM homebot.products WHERE id = $1",
            product_id,
        )
        assert row is None
    finally:
        await conn.execute("ROLLBACK")
        await conn.close()
