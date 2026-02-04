---
name: Homebot PRD Consolidation
overview: Review the Fork Plan chat, identify unique content not in the Compatibility Strategy (master), and update the master plan to incorporate valuable user stories, design decisions, and technical specifications while maintaining Ralph Wiggum compatibility.
todos:
  - id: create-decisions
    content: Create prd/homebot/decisions.md with all DEC-001 through DEC-043+ from Fork Plan
    status: completed
  - id: create-23-tenant
    content: Create prd/homebot/23-multi-tenant.md with MVP essentials + deferred features
    status: completed
  - id: merge-fork-api
    content: Merge Fork Plan custom attributes schemas into 06-api-specification.md
    status: completed
  - id: merge-fork-qr
    content: Merge Fork Plan QR namespace format into 11-qr-routing-system.md
    status: completed
  - id: merge-fork-security
    content: Merge Fork Plan session/RLS patterns into 12-security.md
    status: completed
  - id: archive-fork
    content: Archive Fork Plan chat to prd/archive/ alongside Compat Strategy chat
    status: completed
isProject: false
---

# Homebot PRD Consolidation - Fork Plan Merge

## Summary of Comparison

The **Compatibility Strategy chat** remains the master reference as it was written later and has more complete coverage of:

- Return tracking, Paperless-ngx integration, food intelligence
- Cost tracking/DCA, people/consumption tracking
- Label designer details

The **Fork Plan chat** has valuable unique content that should be merged:

---

## Content to Merge from Fork Plan

### 1. Decision Log Format (DEC-xxx)

The Fork Plan includes 43+ formal decisions in this format:

```markdown
### DEC-001: V2-first API + legacy compatibility engine
- **Decision:** Build `/api/v2/*` as primary, `/api/*` as translation layer
- **Status:** Approved
- **Rationale:** Keeps MVP focused; compat is incremental
- **Phase:** Layer 1 (v2), Layer 2/3 (compat expansion)
```

**Action:** Create `[prd/homebot/decisions.md](prd/homebot/decisions.md)` with all decisions and merge key ones into `[prd/00-Standards-of-Development.md](prd/00-Standards-of-Development.md)`

---

### 2. Multi-Tenant Foundation (MVP Essentials)

The Fork Plan has detailed multi-tenant architecture. Per user direction, include **hard-to-migrate-later essentials** in MVP:

**MVP includes:**

- `tenant_id` column on all core tables (products, locations, stock, etc.)
- `tenants` table with basic info
- `tenant_memberships` table (user-tenant relationships)
- PostgreSQL RLS policies (set `app.tenant_id` per request)
- QR namespace codes include tenant context

**Deferred to later:**

- Tenant switching UI
- Multi-tenant session management
- Cross-tenant transfer workflows

---

### 3. QR Namespace System (Detailed Format)

Fork Plan has concrete specifications:

- **Alphabet:** Crockford Base32 (`0123456789ABCDEFGHJKMNPQRSTVWXYZ`)
- **Format:** `NS-CODE-CHECK` with separators (e.g., `K3D-7K3QF-X`)
- **Namespace:** 3 chars = 32,768 tenants
- **Code:** 5 chars = 33.5M codes per namespace
- **Checksum:** 1 char for validation

**Token states:**

- `unassigned` (preprinted batch)
- `assigned` (bound to container/instance)
- `revoked` (never reused)

---

### 4. Custom Attributes System (OpenAPI Schemas)

Fork Plan has detailed schemas for flexible product attributes:

- `JsonValue` / `JsonPrimitive` recursive schemas
- `Attributes` / `EffectiveAttributes` with inheritance
- `AttributesPatchRequest` with dot-path set/unset operations
- `GET /api/v2/attribute-definitions` endpoint for runtime validation

This provides better detail than Compatibility Strategy and should be merged into `[prd/06-api-specification.md](prd/06-api-specification.md)`

---

### 5. Session/Auth Architecture

Fork Plan has concrete session design:

- Cookie-based session for browser UI (HttpOnly, secure)
- Session stores: `user_id`, `active_tenant_id`, `role`
- Bearer tokens for service-to-service (fixed tenant_id)
- Error responses: `409 tenant_not_selected`, `409 tenant_mismatch`

---

### 6. Cycle Count / Reality-Check Scanning

Fork Plan details the workflow:

1. Select location subtree
2. Enter "scan mode"
3. Scan item tracking codes or product barcodes
4. Compare expected vs observed
5. Generate discrepancy report
6. Apply adjustments

---

### 7. Agent Skills Directory Pattern

Fork Plan recommends:

```
skills/
  test_backend.sh
  lint_backend.sh
  test_frontend.sh
  build_frontend.sh
  reset_db.sh
  migrate_db.sh
  contract_check.sh
  e2e_smoke.sh
```

This aligns well with Ralph Wiggum `test_command` requirements.

---

## Conflicts to Resolve


| Topic                 | Fork Plan       | Compat Strategy | Resolution                                |
| --------------------- | --------------- | --------------- | ----------------------------------------- |
| Multi-tenancy         | Full design     | Not mentioned   | MVP essentials only                       |
| Layer 1/2/3 vs Phases | 3 layers        | 7 phases        | Keep phases (Ralph) with criticality tags |
| Grocy compat          | Separate engine | Facade pattern  | Same concept, merge terminology           |
| Backend               | Python/FastAPI  | Python/FastAPI  | Aligned                                   |
| Frontend              | Quasar          | Vue/Quasar      | Aligned                                   |


---

## Updated Document List

### New Documents to Create


| Document                         | Content                                               |
| -------------------------------- | ----------------------------------------------------- |
| `prd/homebot/decisions.md`       | All DEC-001 through DEC-043+ decisions from Fork Plan |
| `prd/homebot/23-multi-tenant.md` | Multi-tenant architecture (MVP foundation + deferred) |


### Documents to Update with Fork Plan Content


| Document                             | Additional Content from Fork Plan                                       |
| ------------------------------------ | ----------------------------------------------------------------------- |
| `prd/00-Standards-of-Development.md` | Decision log format, skills directory pattern                           |
| `prd/05-data-models.md`              | tenant_id columns, tenants/memberships tables, RLS patterns             |
| `prd/06-api-specification.md`        | Custom attributes schemas, attribute-definitions endpoint, error shapes |
| `prd/11-qr-routing-system.md`        | Crockford Base32, NS-CODE-CHECK format, token states                    |
| `prd/12-security.md`                 | Session architecture, tenant context, RLS policies                      |


---

## Execution Order (Updated)

1. **Create** `prd/homebot/decisions.md` with all Fork Plan decisions
2. **Update** `00-Standards-of-Development.md` (Ralph refs + decision log format)
3. **Update** remaining core docs (01-14) with branding + both chat content
4. **Create** `prd/homebot/23-multi-tenant.md` for multi-tenant design
5. **Create** new feature PRDs in prd/homebot/ (10-22) including Fork Plan content
6. **Create** Ralph phase task docs (80-87) using phase structure with criticality tags
7. **Archive** both chat files to `prd/archive/`

---

## Criticality Tags for Ralph Tasks

Each task criterion will be tagged:

- **[CRITICAL]** - Must be in MVP, hard to change later (e.g., tenant_id columns)
- **[CORE]** - Core functionality for MVP
- **[FLEX]** - Can be deferred without blocking other work
- **[FUTURE]** - Explicitly deferred, design only

This replaces the Layer 1/2/3 concept while being more compatible with Ralph's per-criterion approach.