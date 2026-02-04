# Homebot Development Progress

## Project Status

- **Project:** Homebot (formerly GrocyScan)
- **Current Phase:** Phase 1 - Foundation
- **Phase Documents:** See `prd/80.10-ralph-phases-overview.md`

---

## Previous Project: GrocyScan v1.0.0 (COMPLETE)

GrocyScan v1.0.0 was completed with NiceGUI stack. The project is being rebuilt as Homebot with:
- Vue 3 + Quasar frontend (replacing NiceGUI)
- Multi-tenant architecture with PostgreSQL RLS
- QR code routing and label printing
- Grocy API compatibility layer

---

## Homebot Phase Progress

### Phase 1: Foundation
**Status:** Complete

Criteria:
- [x] [1] PostgreSQL database with homebot schema (migration 0002)
- [x] [2] Tenants table with RLS
- [x] [3] Users table with tenant membership
- [x] [4] Alembic migrations configured
- [x] [5] JWT authentication (POST /api/v2/auth/login)
- [x] [6] API key authentication (HOMEBOT-API-KEY)
- [x] [7] Password hashing with bcrypt
- [x] [8] FastAPI app starts; GET /health returns 200
- [x] [9] OpenAPI spec at /docs
- [x] [10] Basic logging (correlation ID middleware)

### Phase 2: Inventory Core
**Status:** Complete

- Migrations 0003 (products+barcodes), 0004 (locations+closure), 0005 (stock+stock_transactions) in homebot schema.
- v2 API: products (CRUD, search), locations (CRUD, descendants), stock (add, consume, transfer), lookup (barcode).
- RLS and tenant context via X-Tenant-ID and get_db_homebot.

### Phase 3: Device & UI
**Status:** Complete. All 12 criteria [1]–[12] checked; test suite 26 passed, 13 skipped (2026-02-04).

- Migration 0006: homebot.devices. v2 API: POST /api/v2/devices, GET/PATCH /api/v2/devices/me (X-Device-ID). Criteria 4,5,6 done.
- Vue/Quasar frontend: /api/me router mounted. Device registration, action mode, quick actions. Product list with search, product detail with Edit.
- **Criteria 1, 2, 3:** Vue 3 + Quasar is the frontend at :3335. Auth/device state in Pinia stores. Auth guards in Vue Router.
- **Criterion 7:** Camera barcode scanner: BarcodeScanner component with camera button, html5-qrcode, formats UPC/EAN/CODE_128/QR; live camera requires HTTPS and permission.
- **Criterion 12:** PWA: /manifest.json and /sw.js served from app/static/pwa/; manifest link and theme-color in index; service worker registered on load; app installable on supported browsers.

### NiceGUI Deprecation (2026-02-04)
**Status:** Complete

- NiceGUI was used as interim UI during early development
- Removed `app/ui/` directory (~3,500 lines, 14 Python files)
- Removed `nicegui>=1.4.0` from requirements.txt and pyproject.toml
- Updated all PRD documentation to reflect Vue-only architecture
- See DEC-052 in decision log

### Vue/Quasar Frontend (Production)

- **frontend/** : Vue 3 + Quasar v2 + Vite, port 3335, proxy to API 3334. Pinia stores (auth, device), Vue Router with auth guard, Login/Scan/Products/Locations/Settings pages. Device fingerprint in services/device.js. Build: `npm run build`; dev: `npm run dev`.

### Phase 3.5: Inventory Parity
**Status:** Complete (16/17 criteria; [11] Freezer auto-adjust deferred)

- Migration 0011: quantity_units, product_groups, quantity_unit_conversions, enhanced product fields (QU FKs, best-before settings, advanced fields), stock entry enhancements (decimal qty, stock_id, price, open, note), transaction log enhancements (user_id, product_id, correlation_id, undone).
- Stock API: inventory correction, open product, edit stock entry, undo operation with correlation_id support, transfer with correlation_id.
- Location UI: Full CRUD with hierarchy display (3-level), edit/delete dialogs, reorder via sort_order.
- Stock Entry UI: ProductsPage enhanced with stock entry list (expiry indicators, open status), move dialog, inventory correction dialog, mark-as-opened button.
- **Deferred:** [11] Freezer auto-adjust best-before dates on transfer (requires location freezer check in transfer logic).

### Phase 4: Labels & QR
**Status:** Pending (requires Phase 3.5)

### Phase 5: Recipes & Lists
**Status:** Pending (requires Phase 3)

### Phase 6: Intelligence
**Status:** Pending (requires Phases 4, 5)

### Phase 7: Documents & Returns
**Status:** Pending (requires Phase 6)

---

## Session Log

### 2026-02-03
- Phase 1 Foundation implemented: homebot schema migration (tenants, users, tenant_memberships + RLS), API v2 (JWT login, API key), root /health, correlation ID logging, Phase 1 tests (tests/phase1/). All 14 Phase 1 tests pass (11 passed, 3 DB tests skipped without DATABASE_URL=...homebot).
- Phase 2 Inventory Core: migrations 0003 (products+barcodes), 0004 (locations+closure), 0005 (stock+stock_transactions); homebot_models; v2 routes products, locations, stock, lookup; tenant context (X-Tenant-ID, get_db_homebot); SessionMiddleware allows /api/v2/* to use route auth. Phase 2 tests added; all 17 passed (3 skipped).
- Phase 3 Device backend: migration 0006 (homebot.devices), HomebotDevice model, POST /api/v2/devices (register), GET/PATCH /api/v2/devices/me (X-Device-ID), device preferences; Phase 3 tests (test_devices.py). Criteria 4,5,6 complete.

---

## Commits

<!-- Ralph commits will be tracked here -->

### 2026-02-03 12:59:53
**Session 1 started** (model: opus-4.5-thinking)

### 2026-02-03 (browser E2E)
- Full browser E2E: deploy, login (admin/admin), device registration, scan lookup, SPA /scan, Products page.
- **Fix:** Device registration failed with `NoReferencedTableError: ... 'homebot.tenants'`. Added minimal `HomebotTenant` ORM model in `app/db/homebot_models.py` so SQLAlchemy can resolve FKs from devices/products/etc. Deployed; registration and scan flow verified.

### 2026-02-04 (Phase 3.5)
- Migration 0011 created and deployed: quantity_units, product_groups, quantity_unit_conversions tables; product fields (QU FKs, best-before settings, parent, tare, calories, etc.); stock entry enhancements (decimal qty, stock_id, price, open, note); transaction log enhancements (user_id, product_id, correlation_id, undone).
- Stock API v2: inventory correction, open product, edit stock entry, undo transaction with correlation_id support.
- Location UI: Enhanced LocationsPage.vue with hierarchy display, edit dialog, delete confirmation, reorder buttons. Added me.py routes for PATCH/DELETE.
- Phase 3.5 tests: test_stock_operations.py - 6 schema validation tests passing.
