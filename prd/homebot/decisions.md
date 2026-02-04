# Homebot Decision Log

This document records all architectural and design decisions for Homebot. Each decision uses a consistent format to ensure traceability and maintainability.

## Decision Format

```markdown
### DEC-XXX: [Title]
- **Decision:** [What was decided]
- **Status:** [Approved | Proposed | Deferred | Superseded]
- **Rationale:** [Why this decision was made]
- **Phase:** [When to implement: CRITICAL | CORE | FLEX | FUTURE]
- **Notes:** [Additional context]
```

## Criticality Tags

- **[CRITICAL]** - Must be in MVP, hard to change later (e.g., tenant_id columns, database schema)
- **[CORE]** - Core functionality for MVP
- **[FLEX]** - Can be deferred without blocking other work
- **[FUTURE]** - Explicitly deferred, design only

---

# 1. Architecture & API Strategy

### DEC-001: V2-first API + legacy compatibility engine
- **Decision:** Build `/api/v2/*` as the primary API. Implement `/api/*` as a translation/compat layer (engine), not as the core API.
- **Status:** Approved
- **Rationale:** Keeps MVP focused on our needs while allowing "classic Grocy API" compatibility to be incrementally added without distorting the core model.
- **Phase:** 
  - **[CORE]** `/api/v2` only for core flows; no compat required to ship.
  - **[FLEX]** Add selected `/api/*` endpoints used by common integrations.
  - **[FUTURE]** Expand compat coverage + contract tooling.

### DEC-002: Home Assistant integration strategy
- **Decision:** New, custom HA integration targets `/api/v2/*` (no legacy dependence).
- **Status:** Approved
- **Phase:** **[FLEX]** (after barcode-driven inventory flows are solid)

---

# 2. Auth, Tokens, and Agent Tooling

### DEC-003: Service tokens format
- **Decision:** **Opaque bearer service tokens** with scopes, stored hashed, revocable.
- **Status:** Approved
- **Rationale:** Simple revocation, easy scope changes, good for automation/MCP/webhooks.
- **Phase:**
  - **[CORE]** Service tokens + scopes for API + internal tooling.
  - **[FLEX]** Optional user JWT sessions for UI if needed.
  - **[FUTURE]** OAuth/OIDC if desired.

### DEC-004: Bearer auth headers support
- **Decision:** Standard `Authorization: Bearer <token>` for `/api/v2/*`.
- **Status:** Approved
- **Phase:** **[CORE]**

### DEC-005: MCP placement
- **Decision:** Start with **MCP embedded in the backend process** (shared auth/db), with a clean interface so it can be split later.
- **Status:** Approved
- **Rationale:** Fastest path to "tools + resources" while keeping audit/OTel consistent.
- **Phase:**
  - **[FLEX]** Add MCP once core inventory is stable.
  - **[FUTURE]** Split into separate service if warranted.

### DEC-006: Model provider routing
- **Decision:** **Backend brokers model calls** (policy/audit/central config), not frontend direct-to-provider.
- **Status:** Approved
- **Phase:** **[FUTURE]** (not critical path)

---

# 3. Inventory Domain Model

### DEC-007: Product definition vs product instances
- **Decision:** Separate:
  - `products` (definition/catalog)
  - `product_instances` (on-hand, traceable, dated, consumable)
- **Status:** Approved
- **Rationale:** Need exact expiry + consumption + "which one was used".
- **Phase:** **[CRITICAL]**

### DEC-008: Splitting behavior
- **Decision:** Splitting creates **new instances** (never one instance in two places).
- **Status:** Approved
- **Phase:** **[CORE]**

### DEC-009: Consumption selection strategy
- **Decision:** Default consume selection is **FEFO** (first-expired-first-out) for dated instances; barcode scan can override.
- **Status:** Approved
- **Phase:**
  - **[CORE]** FEFO + manual pick.
  - **[FLEX]** "Scan required" mode per product/category.
  - **[FUTURE]** Rule engine for auto-require-scan (e.g., high risk items).

### DEC-010: Instance identifiers for scanning/labels
- **Decision:** Print **QR token URLs** (`/q/<token>`) as the primary tracking code; optionally include a short human code later.
- **Status:** Approved
- **Phase:**
  - **[CORE]** QR token only (fast).
  - **[FLEX]** Add Code128 short code for scanner ergonomics.
  - **[FUTURE]** Encode additional metadata in label templates.

### DEC-011: Prepared dishes
- **Decision:** Prepared dishes are `products` with `kind=prepared_dish`, plus optional extension attributes.
- **Status:** Approved
- **Phase:**
  - **[CORE]** Minimal prepared dish support (name + cooked/frozen dates + portions).
  - **[FLEX]** Ingredients/nutrition decomposition.
  - **[FUTURE]** Recipe scaling, cost rollups, protocol analysis.

---

# 4. Locations & Containers

### DEC-012: Location hierarchy implementation
- **Decision:** Use a **closure table** for locations (deep nesting 5–7, fast subtree reporting/moves).
- **Status:** Approved
- **Phase:** **[CRITICAL]**
- **Notes:** Still store `parent_id` on `locations` for convenience + closure table for queries.

### DEC-013: Ordering within location siblings
- **Decision:** Add `sort_order` now (nullable), use it in UI when present.
- **Status:** Approved
- **Phase:** **[CRITICAL]** (cheap, prevents later migration pain)

### DEC-014: Containers and nesting
- **Decision:** Containers are first-class, **nested 2–3 levels**, with **location inheritance** from parent container.
- **Status:** Approved
- **Phase:** **[CORE]**

### DEC-015: Instance placement model
- **Decision:** `product_instance` belongs to exactly one of:
  - a container, OR
  - a location
- **Status:** Approved
- **Phase:** **[CRITICAL]**
- **Enforcement:** DB constraint: exactly one of `container_id` / `location_id` set.

### DEC-016: Reality-check scanning (cycle count)
- **Decision:** Support a location subtree "scan audit" workflow as an early feature, but minimal MVP.
- **Status:** Approved
- **Phase:**
  - **[CORE]** Scan to locate/consume/add with accurate placement.
  - **[FLEX]** Structured cycle count sessions + discrepancy reports.
  - **[FUTURE]** Automation suggestions and HA/MQTT tie-ins.

---

# 5. Nutrition & Ingredients

### DEC-017: Flexible nutrient/ingredient model
- **Decision:** Use an extensible nutrient dictionary + product nutrient facts with provenance (not a fixed column schema).
- **Status:** Approved
- **Phase:**
  - **[CORE]** Ingredients text + core nutrient slots + provenance scaffold
  - **[FLEX]** Full flexible nutrients + Brave Search enrichment
  - **[FUTURE]** Image analysis OCR + advanced causality heuristics

### DEC-018: Automated enrichment sources priority
- **Decision:** Start with structured sources (Open Food Facts/UPC). Add Brave Search next. Add image OCR later.
- **Status:** Approved
- **Phase:** As above

### DEC-019: Diet/allergy/protocol flags
- **Decision:** Implement flags as explainable, auditable "signals", user-overridable.
- **Status:** Approved
- **Phase:**
  - **[CORE]** Basic allergens/diet tags manual + simple parsing
  - **[FLEX]** Rules engine + cited sources
  - **[FUTURE]** Personal sensitivity model + longitudinal analysis

---

# 6. Photos & Media

### DEC-020: Product photo capture/import
- **Decision:** Support:
  - Camera capture (mobile)
  - File upload (desktop)
  - URL import (web scrape/download)
  - USB webcam (browser getUserMedia)
- **Status:** Approved
- **Phase:**
  - **[CORE]** Upload + camera capture + store in volume; show in UI
  - **[FLEX]** URL import + dedupe + thumbnails
  - **[FUTURE]** Image analysis pipeline

---

# 7. Observability & Audit

### DEC-021: Observability stack
- **Decision:** OpenTelemetry everywhere (backend required), export via OTLP to a collector; keep dev "batteries included" via compose profile.
- **Status:** Approved
- **Phase:**
  - **[CORE]** Backend traces + request IDs + basic logs
  - **[FLEX]** Collector + tempo/jaeger + loki + dashboards
  - **[FUTURE]** SLOs/alerts

### DEC-022: Audit logs
- **Decision:** Append-only audit log for all mutations with actor attribution.
- **Status:** Approved
- **Phase:** **[CRITICAL]** (because it supports correctness and later agents)

### DEC-023: Log streaming
- **Decision:** SSE-based streaming for long jobs (migration, enrichment, printing).
- **Status:** Approved
- **Phase:** **[FLEX]** (unless enrichment is in MVP; then include minimal streaming)

---

# 8. Reporting & Dashboards

### DEC-024: Reporting approach
- **Decision:** MVP includes:
  - Curated built-in reports + CSV export
  - Report "cards" as dashboard building blocks
- **Status:** Approved
- **Phase:** **[FLEX]**

### DEC-025: Template-based reports
- **Decision:** Start with **admin-authored parameterized SQL templates (read-only)** for power and speed, plus CSV export. Consider a DSL later.
- **Status:** Approved
- **Phase:**
  - **[FLEX]** SQL templates + parameters + CSV
  - **[FUTURE]** DSL/query builder + user-authored templates

---

# 9. Costing & Receipts

### DEC-026: Costing method
- **Decision:** Start with **specific identification** at `product_instance` level (cost comes from receipt line / manual). Add rollups later.
- **Status:** Approved
- **Phase:**
  - **[FLEX]** Record purchase price + retailer + date per instance
  - **[FUTURE]** Average/FIFO valuation + recipe/meal costing + trend reports

### DEC-027: Retailer links + price intelligence
- **Decision:** Store retailer as first-class entity and allow links (Amazon/etc). Add Brave Search price lookup later with caching/provenance.
- **Status:** Approved
- **Phase:** **[FUTURE]** (unless quick "last price" in FLEX)

### DEC-028: Paperless-ngx receipts linking
- **Decision:** Support linking by explicit document ID/URL first; add OCR/tag matching later.
- **Status:** Approved
- **Phase:**
  - **[FLEX]** Manual link fields
  - **[FUTURE]** Automatic matching

---

# 10. Technology Stack

### DEC-029: Backend framework + ORM stack
- **Decision:** FastAPI + SQLAlchemy 2.0 + Alembic + Pydantic v2.
- **Status:** Approved
- **Phase:** **[CRITICAL]**

### DEC-030: Frontend grid choice per screen
- **Decision:** Quasar QTable for light lists; AG Grid Community for heavy editing (instances, stock journal, reports).
- **Status:** Approved
- **Phase:** **[CORE]**

### DEC-031: Storage for photos
- **Decision:** Filesystem volume in Docker (`/data/media`) with generated thumbnails; later S3-compatible.
- **Status:** Approved
- **Phase:** **[CORE]**

### DEC-032: Barcode scanning library
- **Decision:** html5-qrcode for camera scanning + hidden input capture for Bluetooth scanners.
- **Status:** Approved
- **Phase:** **[CORE]**

---

# 11. Multi-Tenant Architecture

### DEC-033: Tenant ID on all tables
- **Decision:** Include `tenant_id` column on all core tables from day one (products, locations, stock, containers, etc.).
- **Status:** Approved
- **Rationale:** Hard to migrate later; schema must support multi-tenancy even if single-tenant in MVP.
- **Phase:** **[CRITICAL]**

### DEC-034: Tenant tables structure
- **Decision:** Create `tenants` table and `tenant_memberships` table for user-tenant relationships.
- **Status:** Approved
- **Phase:** **[CRITICAL]**

### DEC-035: PostgreSQL RLS policies
- **Decision:** Enable Row-Level Security on all tenant tables. Set `app.tenant_id` session variable per request.
- **Status:** Approved
- **Phase:** **[CRITICAL]**

### DEC-036: Tenant switching UI
- **Decision:** Defer complex tenant switching UI and multi-tenant session management to later phase.
- **Status:** Approved
- **Phase:** **[FUTURE]**

### DEC-037: Cross-tenant transfers
- **Decision:** Not in MVP. If added later, transfers mint new tenant-owned tokens for transferred instances/containers.
- **Status:** Approved
- **Rationale:** Avoids weakening tenant boundary and avoids "labels that change meaning".
- **Phase:** **[FUTURE]**

---

# 12. QR Code & Token System

### DEC-038: QR code alphabet
- **Decision:** Use Crockford Base32 alphabet: `0123456789ABCDEFGHJKMNPQRSTVWXYZ` (no I, L, O, U).
- **Status:** Approved
- **Rationale:** Avoids confusing characters for human readability.
- **Phase:** **[CORE]**

### DEC-039: QR code format
- **Decision:** Format is `NS-CODE-CHECK` with separators (e.g., `K3D-7K3QF-X`).
- **Status:** Approved
- **Phase:** **[CORE]**

### DEC-040: QR code lengths
- **Decision:**
  - Namespace (NS): 3 chars = 32,768 possible namespaces
  - Code: 5 chars = 33,554,432 codes per namespace
  - Checksum: 1 char for validation
- **Status:** Approved
- **Phase:** **[CORE]**

### DEC-041: Namespace length
- **Decision:** Fixed **3-character** Crockford Base32 namespace code (per tenant default namespace).
- **Status:** Approved
- **Rationale:** Enough tenant capacity without long labels.
- **Phase:** **[CORE]**

### DEC-042: Cross-tenant transfer token policy
- **Decision:** If/when cross-tenant transfer is implemented, we **mint a new token** in the destination tenant and (optionally) print a new label. No token `tenant_id` reassignment.
- **Status:** Approved
- **Rationale:** Preserves RLS boundaries and prevents old physical labels from "changing meaning".
- **Phase:** **[FUTURE]**

### DEC-043: Human-readable formatting
- **Decision:** Include separators in printed/human-visible code (`NS-CODE-CHECK`). UI accepts input with or without separators (normalize on ingest).
- **Status:** Approved
- **Phase:** **[CORE]**

### DEC-044: Token states
- **Decision:** QR tokens have states:
  - `unassigned` (preprinted batch)
  - `assigned` (bound to container or product_instance)
  - `revoked` (never reused)
- **Status:** Approved
- **Phase:** **[CORE]**

---

# 13. Session & Authentication Architecture

### DEC-045: Browser session mechanism
- **Decision:** Cookie-based session for browser UI (HttpOnly, secure). Session stores: `user_id`, `active_tenant_id`, `role`.
- **Status:** Approved
- **Phase:** **[CORE]**

### DEC-046: Service token tenant binding
- **Decision:** Bearer tokens for service-to-service have fixed `tenant_id` (never switch).
- **Status:** Approved
- **Phase:** **[CORE]**

### DEC-047: Tenant error responses
- **Decision:** Use specific error codes:
  - `409 tenant_not_selected` - No active tenant in session
  - `409 tenant_mismatch` - QR/resource belongs to different tenant
- **Status:** Approved
- **Phase:** **[FLEX]**

---

# 14. Custom Attributes System

### DEC-048: Flexible attributes storage
- **Decision:** Store custom attributes as JSONB with nested structure. Use dot-path addressing for API operations.
- **Status:** Approved
- **Phase:** **[CORE]**

### DEC-049: Effective attributes inheritance
- **Decision:** Product instances inherit attributes from product definitions. Instance attributes override product-level attributes.
- **Status:** Approved
- **Phase:** **[CORE]**

### DEC-050: Attribute definitions endpoint
- **Decision:** Provide `GET /api/v2/attribute-definitions` endpoint for runtime validation with:
  - Namespace rules
  - Value schemas (JSON Schema fragments)
  - UI hints (label, component, options)
- **Status:** Approved
- **Phase:** **[FLEX]**

---

# Summary by Criticality

## CRITICAL (Must be in MVP schema)
- DEC-007: Product definition vs product instances
- DEC-012: Location hierarchy (closure table)
- DEC-013: Ordering within location siblings
- DEC-015: Instance placement model
- DEC-022: Audit logs
- DEC-029: Backend framework (FastAPI + SQLAlchemy)
- DEC-033: Tenant ID on all tables
- DEC-034: Tenant tables structure
- DEC-035: PostgreSQL RLS policies

## CORE (MVP functionality)
- DEC-001: V2-first API
- DEC-003: Service tokens
- DEC-004: Bearer auth headers
- DEC-008: Splitting behavior
- DEC-009: Consumption FEFO
- DEC-010: QR token URLs
- DEC-011: Prepared dishes (minimal)
- DEC-014: Containers and nesting
- DEC-016: Reality-check scanning (basic)
- DEC-017: Nutrient model (basic)
- DEC-019: Diet/allergy flags (basic)
- DEC-020: Product photos
- DEC-021: Observability (basic)
- DEC-030-032: Frontend, storage, barcode library
- DEC-038-044: QR code system
- DEC-045-046: Session architecture
- DEC-048-049: Custom attributes

## FLEX (Can be deferred)
- DEC-002: Home Assistant integration
- DEC-005: MCP server
- DEC-016: Cycle count sessions
- DEC-023: Log streaming
- DEC-024-025: Reporting & dashboards
- DEC-026-028: Costing & receipts
- DEC-047: Tenant error responses
- DEC-050: Attribute definitions endpoint

## FUTURE (Design only)
- DEC-006: Model provider routing
- DEC-036: Tenant switching UI
- DEC-037, DEC-042: Cross-tenant transfers
