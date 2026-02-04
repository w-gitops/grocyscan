# 23. Multi-Tenant Architecture

## Overview

Homebot is designed with multi-tenant architecture from day one. While the MVP may operate as single-tenant, the database schema and security model must support multi-tenancy to avoid costly retrofits later.

This document covers:
- MVP essentials (must be in initial schema)
- Deferred features (design only, implement later)
- Implementation patterns

---

## Related Decisions

See [decisions.md](decisions.md) for detailed decision records:
- DEC-033: Tenant ID on all tables
- DEC-034: Tenant tables structure
- DEC-035: PostgreSQL RLS policies
- DEC-036: Tenant switching UI (deferred)
- DEC-037: Cross-tenant transfers (deferred)

---

## 1. MVP Essentials (CRITICAL)

These components must be in the initial schema to avoid migration pain later.

### 1.1 Core Tenant Tables

#### `tenants`

```sql
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bootstrap default tenant on first install
INSERT INTO tenants (slug, name) VALUES ('default', 'My Home');
```

#### `users`

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### `tenant_memberships`

```sql
CREATE TABLE tenant_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    user_id UUID NOT NULL REFERENCES users(id),
    role VARCHAR(50) NOT NULL DEFAULT 'member', -- 'admin', 'member'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (tenant_id, user_id)
);
```

### 1.2 Tenant ID on All Core Tables

Every tenant-owned table must include a `tenant_id` column:

```sql
-- Example: products table
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    name VARCHAR(255) NOT NULL,
    -- ... other columns
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_products_tenant ON products(tenant_id);
```

**Tables requiring `tenant_id`:**

| Category | Tables |
|----------|--------|
| Core Inventory | `products`, `product_barcodes`, `product_instances`, `locations`, `location_closure`, `containers` |
| QR System | `qr_namespaces`, `qr_tokens`, `qr_batches` |
| Nutrition | `ingredients`, `nutrients`, `product_nutrients` |
| Labels | `print_templates`, `print_jobs` |
| Audit | `audit_log` |
| User Data | `device_preferences`, `report_templates` |

**Tables that may be global (no tenant_id):**

- `migrations` (system)
- `nutrient_definitions` (shared reference data)
- System configuration

### 1.3 PostgreSQL Row-Level Security (RLS)

Enable RLS on all tenant tables from day one.

#### Setting Tenant Context

Every request must set the tenant context before executing queries:

```sql
SET LOCAL app.tenant_id = '<tenant_uuid>';
```

In FastAPI/SQLAlchemy:

```python
from sqlalchemy.orm import Session
from fastapi import Depends

async def set_tenant_context(
    db: Session,
    tenant_id: str
):
    """Set tenant context for RLS."""
    db.execute(text(f"SET LOCAL app.tenant_id = '{tenant_id}'"))
```

#### RLS Policy Pattern

For each tenant-owned table:

```sql
-- Enable RLS
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE products FORCE ROW LEVEL SECURITY;

-- Create isolation policy
CREATE POLICY products_tenant_isolation ON products
    USING (tenant_id = current_setting('app.tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid);
```

- `USING` - Controls which rows are visible (SELECT, UPDATE, DELETE)
- `WITH CHECK` - Controls which rows can be inserted/updated
- `FORCE ROW LEVEL SECURITY` - Ensures even table owners obey policies

### 1.4 QR Namespaces

Each tenant has one or more QR namespaces for labeling.

```sql
CREATE TABLE qr_namespaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    code VARCHAR(4) NOT NULL, -- 3-char Crockford Base32
    name VARCHAR(255),
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (code) -- Globally unique namespace codes
);
```

### 1.5 Service Tokens with Tenant Binding

Service tokens are always bound to a specific tenant:

```sql
CREATE TABLE service_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE service_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_account_id UUID NOT NULL REFERENCES service_accounts(id),
    token_hash VARCHAR(255) NOT NULL, -- bcrypt hash of token
    scopes TEXT[], -- Array of scope strings
    expires_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 2. Database Roles

Use separate database roles for different contexts:

### 2.1 Application Role (RLS enforced)

```sql
CREATE ROLE app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
```

The application uses this role for all runtime queries. RLS is enforced.

### 2.2 Migration Role (RLS bypassed)

```sql
CREATE ROLE migration_user BYPASSRLS;
GRANT ALL ON ALL TABLES IN SCHEMA public TO migration_user;
```

Used by Alembic for migrations. Can bypass RLS when needed.

### 2.3 Connection Pattern

```python
# Application connections
app_engine = create_engine(DATABASE_URL, connect_args={"options": "-c role=app_user"})

# Migration connections
migration_engine = create_engine(DATABASE_URL, connect_args={"options": "-c role=migration_user"})
```

---

## 3. Deferred Features (FUTURE)

These features are designed but not implemented in MVP.

### 3.1 Tenant Switching UI

**Design:**
1. User logs in
2. If user has memberships in multiple tenants, show tenant picker
3. Selected tenant becomes `active_tenant_id` in session
4. Tenant chip in app bar shows current tenant and allows switching

**API Endpoints:**

```
POST /api/v2/auth/login
  Response: { user, tenants[], active_tenant_id }

GET /api/v2/auth/session
  Response: { user, tenants[], active_tenant_id }

POST /api/v2/tenants/switch
  Request: { tenant_id }
  Response: { active_tenant_id }

GET /api/v2/tenants
  Response: { tenants[] }
```

**Session Storage:**

```python
class SessionData:
    user_id: str
    active_tenant_id: str
    active_membership_role: str  # 'admin' or 'member'
```

### 3.2 QR Scan with Tenant Mismatch

When scanning a QR from a different tenant:

1. Resolve namespace → tenant from QR code
2. If user is logged in and tenant differs from active:
   - Show modal: "This label belongs to [Tenant Name]. Switch?"
   - Options: "Switch & Continue" or "Cancel"
3. If user is not logged in:
   - Redirect to login with `next` parameter
   - After login, show tenant picker if needed

**Error Responses:**

```json
// HTTP 409 - Tenant not selected
{
  "error": "tenant_not_selected",
  "tenants": [{ "tenant_id": "...", "name": "Home" }]
}

// HTTP 409 - Tenant mismatch
{
  "error": "tenant_mismatch",
  "required_tenant_id": "t2",
  "current_tenant_id": "t1"
}
```

### 3.3 Cross-Tenant Transfers

**Policy:** If cross-tenant transfer is implemented:
- Create new instance/container record in destination tenant
- Mint new QR token in destination namespace
- Old token in source tenant remains pointing to archived record
- Never reassign token's `tenant_id`

**Rationale:** Preserves RLS boundaries and prevents labels from "changing meaning".

---

## 4. Implementation Checklist

### MVP (Phase 1)

- [ ] Create `tenants` table
- [ ] Create `users` table
- [ ] Create `tenant_memberships` table
- [ ] Add `tenant_id` to all core tables
- [ ] Create indexes on `tenant_id` columns
- [ ] Enable RLS on all tenant tables
- [ ] Create RLS policies for each table
- [ ] Create `app_user` and `migration_user` roles
- [ ] Add tenant context middleware to FastAPI
- [ ] Bootstrap default tenant on install
- [ ] Create `qr_namespaces` table
- [ ] Create `service_accounts` and `service_tokens` tables

### Tests (MVP)

- [ ] Test: Two tenants can have products with same name
- [ ] Test: Queries without tenant context fail
- [ ] Test: Token in tenant A cannot resolve tenant B objects
- [ ] Test: Service token is restricted to its tenant
- [ ] Test: RLS prevents cross-tenant data access

### Future Phases

- [ ] Tenant picker UI component
- [ ] Tenant switching API endpoints
- [ ] QR scan tenant mismatch handling
- [ ] Cross-tenant transfer workflow

---

## 5. Alembic Migration Pattern

Standard pattern for adding tenant_id to new tables:

```python
# migrations/versions/xxx_add_new_table.py

def upgrade():
    op.create_table(
        'new_table',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
    )
    op.create_index('idx_new_table_tenant', 'new_table', ['tenant_id'])
    
    # Enable RLS
    op.execute('ALTER TABLE new_table ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE new_table FORCE ROW LEVEL SECURITY')
    
    # Create policy
    op.execute("""
        CREATE POLICY new_table_tenant_isolation ON new_table
        USING (tenant_id = current_setting('app.tenant_id')::uuid)
        WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid)
    """)

def downgrade():
    op.execute('DROP POLICY IF EXISTS new_table_tenant_isolation ON new_table')
    op.drop_table('new_table')
```

---

## 6. FastAPI Middleware Example

```python
from fastapi import Request, HTTPException
from sqlalchemy import text

async def tenant_context_middleware(request: Request, call_next):
    """Set tenant context for all database operations."""
    
    # Skip for public endpoints
    if request.url.path.startswith("/api/v2/auth") or request.url.path.startswith("/q/"):
        return await call_next(request)
    
    # Get tenant_id from session or token
    tenant_id = None
    
    # Check bearer token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        tenant_id = await resolve_tenant_from_token(token)
    
    # Check session cookie
    if not tenant_id:
        session = request.state.session
        tenant_id = session.get("active_tenant_id") if session else None
    
    if not tenant_id:
        raise HTTPException(status_code=409, detail={
            "error": "tenant_not_selected",
            "message": "No active tenant in session"
        })
    
    # Store for use in route handlers
    request.state.tenant_id = tenant_id
    
    return await call_next(request)


# Database session dependency
async def get_db_with_tenant(request: Request):
    """Get database session with tenant context set."""
    async with AsyncSession(engine) as session:
        tenant_id = request.state.tenant_id
        await session.execute(text(f"SET LOCAL app.tenant_id = '{tenant_id}'"))
        yield session
```

---

## Tasks Summary

Tasks derived from this PRD for Ralph execution:

| Task ID | Description | Phase | Priority |
|---------|-------------|-------|----------|
| HB-MT-01 | Create tenants, users, tenant_memberships tables | 1 | P0 |
| HB-MT-02 | Add tenant_id to all core tables | 1 | P0 |
| HB-MT-03 | Enable RLS and create policies | 1 | P0 |
| HB-MT-04 | Create tenant context middleware | 1 | P0 |
| HB-MT-05 | Create qr_namespaces table | 1 | P0 |
| HB-MT-06 | Write tenant isolation tests | 1 | P0 |
| HB-MT-07 | Implement tenant switching UI | 3+ | P2 |
| HB-MT-08 | Implement QR tenant mismatch handling | 3+ | P2 |
