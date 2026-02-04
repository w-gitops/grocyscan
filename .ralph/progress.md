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
**Status:** In progress (device backend + NiceGUI scan UI)

- Migration 0006: homebot.devices. v2 API: POST /api/v2/devices, GET/PATCH /api/v2/devices/me (X-Device-ID). Criteria 4,5,6 done.
- Option A (NiceGUI): /api/me router mounted. Device registration prompt on scan page (GET /api/me/device → 404 shows dialog, POST register). Action mode row (Add Stock | Consume | Transfer) with PATCH default_action. Quick actions: after scan, GET /api/me/product-by-barcode; if in homebot show +1/-1 calling /api/me/stock/add and /api/me/stock/consume. Criteria 8, 9 done.
- **Criteria 10, 11 done:** Products page: Homebot tab lists products from GET /api/me/products with client-side search (name/description/category). Product detail: click row opens dialog with stock by location; Edit button opens form, PATCH /api/me/products/{id} for name/description/category. API base uses relative URLs for deployment. Frontend scaffold (1,2,3), camera (7), PWA (12) pending.
- Deploy: Ran scripts/deploy.ps1; app and migrations synced to 192.168.200.37, grocyscan service restarted (active). Scanner validation: https://grocyscan.ssiops.com returned 502 Bad Gateway; direct 192.168.200.37:3334 and localhost:3334 connection refused from browser host. Scanner UI (BarcodeScanner with camera button, html5-qrcode, manual input) is deployed; live camera validation requires app reachable (fix proxy/502 or test from LAN).

### Phase 4: Labels & QR
**Status:** Pending (requires Phase 3)

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
