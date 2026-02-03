---
task: Homebot Phase 2 - Inventory Core
test_command: pytest tests/phase2/ tests/phase1/ -v --tb=short
browser_validation: false
---

# Task: Homebot Phase 2 - Inventory Core

Products, locations, stock tracking, and barcode scanning.

**PRD Reference:** [prd/80.12-ralph-phase-2-inventory.md](prd/80.12-ralph-phase-2-inventory.md)

## Success Criteria

### Products

- [x] Products table with all required fields <!-- group: 1 -->
- [x] Product CRUD endpoints <!-- group: 1 -->
- [x] Product search by name, barcode, category <!-- group: 1 -->

### Locations

- [x] Locations table with hierarchy support <!-- group: 2 -->
- [x] Location closure table for efficient queries <!-- group: 2 -->
- [x] Location CRUD with hierarchy management <!-- group: 2 -->

### Stock Management

- [x] Stock tracking table <!-- group: 3 -->
- [x] Add stock endpoint <!-- group: 3 -->
- [x] Consume stock endpoint <!-- group: 3 -->
- [x] Transfer stock between locations <!-- group: 3 -->

### Barcode Lookup

- [x] OpenFoodFacts integration <!-- group: 4 -->
- [x] UPC Database fallback (via existing lookup manager) <!-- group: 4 -->

---

## Context

- **Deploy Target:** `192.168.200.37` via SSH (root)
- **Install Path:** `/opt/grocyscan/` (or `/opt/homebot/`)
- **Service:** `grocyscan` (systemd)
- **Port:** 3334

## Technical Notes

- Phase 2 migrations: 0003 (products+barcodes), 0004 (locations+closure), 0005 (stock+stock_transactions) in homebot schema.
- v2 API requires `X-Tenant-ID` header and JWT or `HOMEBOT-API-KEY` for inventory endpoints.
- Session middleware allows `/api/v2/*` through; route dependencies enforce Bearer/API key.

## Phase Navigation

| Phase | Document | Status |
|-------|----------|--------|
| 1 | [Foundation](prd/80.11-ralph-phase-1-foundation.md) | Complete |
| 2 | [Inventory](prd/80.12-ralph-phase-2-inventory.md) | **Current** |
| 3 | [Device UI](prd/80.13-ralph-phase-3-device-ui.md) | Pending |
| 4 | [Labels & QR](prd/80.14-ralph-phase-4-labels-qr.md) | Pending |
| 5 | [Recipes](prd/80.15-ralph-phase-5-recipes.md) | Pending |
| 6 | [Intelligence](prd/80.16-ralph-phase-6-intelligence.md) | Pending |
| 7 | [Documents](prd/80.17-ralph-phase-7-documents.md) | Pending |
