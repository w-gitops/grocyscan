# 12. Security Requirements

## Related Documents

- [23-multi-tenant.md](homebot/23-multi-tenant.md) - Multi-tenant architecture details
- [decisions.md](homebot/decisions.md) - Security-related decisions (DEC-003, DEC-004, DEC-033-037, DEC-045-047)

---

## 12.1 Authentication

| Requirement | Implementation |
|-------------|----------------|
| **Password Hashing** | bcrypt with cost factor 12 |
| **Session Management** | Server-side sessions with secure cookies |
| **Session Timeout** | 24 hours idle, 7 days absolute |
| **CSRF Protection** | Token-based CSRF protection on all forms |

### 12.1.1 Session Architecture

Homebot uses cookie-based sessions for browser clients and bearer tokens for API/automation.

**Browser Sessions:**

```python
class SessionData:
    """Server-side session data stored in Redis/database."""
    user_id: UUID
    active_tenant_id: UUID
    active_membership_role: str  # 'admin' or 'member'
    csrf_token: str
    created_at: datetime
    last_accessed: datetime
```

**Cookie Configuration:**

```python
session_cookie = SessionCookie(
    name="homebot_session",
    httponly=True,
    secure=True,  # Requires HTTPS
    samesite="lax",
    max_age=86400 * 7  # 7 days
)
```

### 12.1.2 Service Token Authentication

Service tokens for API/automation access:

| Property | Value |
|----------|-------|
| Header | `Authorization: Bearer <token>` |
| Storage | Hashed (bcrypt) in database |
| Revocation | Immediate via database flag |
| Tenant Binding | Fixed to one tenant |
| Scopes | Array of permission strings |

```python
class ServiceToken:
    id: UUID
    service_account_id: UUID
    token_hash: str  # bcrypt hash
    scopes: list[str]  # e.g., ['products:read', 'stock:write']
    expires_at: Optional[datetime]
    revoked_at: Optional[datetime]
```

### 12.1.3 Grocy API Compatibility

For `/api/*` compatibility routes, also accept:

- Header: `GROCY-API-KEY: <key>`
- Query param: `?GROCY-API-KEY=<key>` (legacy support)

## 12.2 API Security

| Requirement | Implementation |
|-------------|----------------|
| **Rate Limiting** | 100 requests/minute per IP |
| **Input Validation** | Pydantic models with strict validation |
| **SQL Injection** | Parameterized queries via SQLAlchemy ORM |
| **XSS Prevention** | Content Security Policy headers |

## 12.3 Multi-Tenant Security (Row-Level Security)

### 12.3.1 Tenant Context

Every database operation runs within a tenant context enforced by PostgreSQL RLS.

**Setting Context:**

```python
async def set_tenant_context(db: AsyncSession, tenant_id: UUID):
    """Set tenant context for RLS enforcement."""
    await db.execute(text(f"SET LOCAL app.tenant_id = '{tenant_id}'"))
```

**Middleware Pattern:**

```python
@app.middleware("http")
async def tenant_context_middleware(request: Request, call_next):
    # Extract tenant_id from session or bearer token
    tenant_id = await resolve_tenant_id(request)
    
    if tenant_id is None and not is_public_route(request.url.path):
        raise HTTPException(409, detail={
            "error": "tenant_not_selected",
            "message": "No active tenant in session"
        })
    
    request.state.tenant_id = tenant_id
    return await call_next(request)
```

### 12.3.2 RLS Policy Pattern

Every tenant-owned table has RLS enabled:

```sql
-- Enable RLS
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE products FORCE ROW LEVEL SECURITY;

-- Isolation policy
CREATE POLICY products_tenant_isolation ON products
    USING (tenant_id = current_setting('app.tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid);
```

**Tables with RLS:**
- `products`, `product_barcodes`, `product_instances`
- `locations`, `location_closure`, `containers`
- `qr_namespaces`, `qr_tokens`, `qr_batches`
- `audit_log`, `print_templates`, `print_jobs`
- All tenant-owned data tables

### 12.3.3 Database Roles

| Role | Purpose | RLS |
|------|---------|-----|
| `app_user` | Runtime application queries | Enforced |
| `migration_user` | Alembic migrations | Bypassed |

```sql
CREATE ROLE app_user;
CREATE ROLE migration_user BYPASSRLS;
```

### 12.3.4 Tenant Mismatch Handling

When accessing a resource from a different tenant:

```json
// HTTP 409 Response
{
  "error": "tenant_mismatch",
  "message": "This resource belongs to a different tenant",
  "required_tenant_id": "uuid-2",
  "current_tenant_id": "uuid-1"
}
```

The UI should prompt the user to switch tenants (if they have access) or show an error.

## 12.3 Secrets Management

```python
# app/config.py
from pydantic_settings import BaseSettings
from pydantic import SecretStr

class Settings(BaseSettings):
    """Application settings with secure secret handling."""
    
    # Secrets are never logged or exposed
    SECRET_KEY: SecretStr
    DATABASE_URL: SecretStr
    GROCY_API_KEY: SecretStr
    LLM_API_KEY: SecretStr = SecretStr("")
    BRAVE_API_KEY: SecretStr = SecretStr("")
    GOUPC_API_KEY: SecretStr = SecretStr("")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

## 12.4 Network Security

| Requirement | Implementation |
|-------------|----------------|
| **TLS Termination** | At reverse proxy (Caddy/Traefik) |
| **Internal Communication** | HTTP within Docker network only |
| **Grocy API URL** | Separate internal vs external URLs |
| **CORS** | Restricted to configured origins |

## 12.5 API Key Authentication for External Access

```python
# app/api/auth.py
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key for external application access."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    valid_key = await validate_api_key(api_key)
    if not valid_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    return valid_key
```

## 12.6 QR Code Security

### 12.6.1 Token Enumeration Protection

- Tokens use random 5-character Crockford Base32 codes
- 33+ million possible values per namespace
- Checksum digit detects typos but not guessing
- Sequential minting is NOT used

### 12.6.2 Token Resolution Security

The `/q/{code}` endpoint:
- Does NOT reveal token details without authentication
- Returns 404 for invalid, revoked, or nonexistent tokens
- Does NOT leak tenant information to unauthenticated users
- Sets tenant context before any database queries

### 12.6.3 Namespace Isolation

- Each tenant has unique namespace codes
- Namespace codes are globally unique (no collisions)
- Cross-namespace token lookup is impossible via RLS

## 12.7 Audit Logging

### 12.7.1 Audit Requirements

All mutations create audit log entries:

```python
class AuditEntry:
    id: UUID
    tenant_id: UUID
    actor_type: str  # 'user', 'service_token', 'system'
    actor_id: UUID
    action: str  # 'CREATE_PRODUCT', 'CONSUME_STOCK', etc.
    entity_type: str
    entity_id: UUID
    before_state: Optional[dict]
    after_state: Optional[dict]
    request_id: UUID  # For trace correlation
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: datetime
```

### 12.7.2 Audit Storage

- Append-only table (no updates or deletes)
- Partitioned by month for performance
- RLS enforced (tenants only see their own logs)
- Retention policy: configurable (default 365 days)

## 12.8 Security Checklist

### Authentication & Sessions
- [ ] All secrets stored in environment variables
- [ ] Database credentials use strong passwords
- [ ] API keys have minimum required permissions
- [ ] Session cookies marked as HttpOnly and Secure
- [ ] Service tokens stored hashed (bcrypt)
- [ ] Token revocation is immediate

### Multi-Tenant Security
- [ ] `tenant_id` column on all tenant tables
- [ ] RLS enabled on all tenant tables
- [ ] `FORCE ROW LEVEL SECURITY` applied
- [ ] Tenant context set before every query
- [ ] Queries without tenant context fail loudly
- [ ] Cross-tenant access tests pass

### Network Security
- [ ] TLS enabled for all external connections
- [ ] CORS configured to allow only trusted origins
- [ ] Rate limiting enabled on all endpoints
- [ ] Internal services not exposed externally

### Data Security
- [ ] Input validation on all user inputs
- [ ] Logs do not contain sensitive data
- [ ] Audit logs capture all mutations
- [ ] Dependencies scanned for vulnerabilities

### QR Code Security
- [ ] Token enumeration not feasible
- [ ] Revoked tokens return 404
- [ ] No tenant info leaked to unauthenticated users

---

## Tasks Summary

Tasks derived from this PRD for Ralph execution:

| Task ID | Description | Phase | Priority |
|---------|-------------|-------|----------|
| HB-SEC-01 | Implement session management with tenant context | 1 | P0 |
| HB-SEC-02 | Create service token authentication | 1 | P0 |
| HB-SEC-03 | Enable RLS on all tenant tables | 1 | P0 |
| HB-SEC-04 | Create tenant context middleware | 1 | P0 |
| HB-SEC-05 | Implement audit logging | 1 | P0 |
| HB-SEC-06 | Add Grocy API key compatibility | 2 | P1 |
| HB-SEC-07 | Write tenant isolation tests | 1 | P0 |

---

## Navigation

- **Previous:** [Schema Evolution](11-schema-evolution.md)
- **Next:** [Project Standards](13-project-standards.md)
- **Back to:** [README](README.md)
