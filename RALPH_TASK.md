---
task: Homebot Phase 3.5 - Inventory Parity
test_command: pytest tests/phase3_5/ tests/phase3/ tests/phase2/ -v --tb=short
browser_validation: true
browser_url: http://localhost:3335
---

# Task: Homebot Phase 3.5 - Inventory Parity

Full Grocy inventory parity - quantity units, stock operations, location UI, undo.

**PRD Reference:** [prd/80.135-ralph-phase-3.5-inventory-parity.md](prd/80.135-ralph-phase-3.5-inventory-parity.md)

## Success Criteria

### Database Schema (Migration 0011)

- [x] **[1]** Quantity units table and product quantity unit FKs
- [x] **[2]** Product best-before settings
- [x] **[3]** Product advanced fields
- [x] **[4]** Stock entry enhancements (decimal qty, stock_id, price, open, note)
- [x] **[5]** Transaction log enhancements (user_id, correlation_id, undone)
- [x] **[6]** Product groups table

### Stock Operations API

- [x] **[7]** Inventory operation (set stock to specific amount)
- [x] **[8]** Open product operation
- [x] **[9]** Edit stock entry
- [x] **[10]** Undo operation
- [ ] **[11]** Freezer auto-adjust best-before dates

### Location Management UI (Vue/Quasar)

- [x] **[12]** Location list with hierarchy
- [x] **[13]** Location CRUD in UI (edit/delete)
- [x] **[14]** Reorder locations

### Stock Entry UI (Vue/Quasar)

- [x] **[15]** View stock entries for product
- [x] **[16]** Move stock dialog
- [x] **[17]** Inventory correction dialog

---

## Context

- **Deploy Target:** `192.168.200.37` via SSH (root)
- **Install Path:** `/opt/grocyscan/`
- **Port:** 3334 (API), 3335 (Vue dev)
- **Public URL:** `https://grocyscan.ssiops.com`

## Phase Navigation

| Phase | Document | Status |
|-------|----------|--------|
| 1 | [Foundation](prd/80.11-ralph-phase-1-foundation.md) | Complete |
| 2 | [Inventory](prd/80.12-ralph-phase-2-inventory.md) | Complete |
| 3 | [Device & UI](prd/80.13-ralph-phase-3-device-ui.md) | Complete |
| 3.5 | [Inventory Parity](prd/80.135-ralph-phase-3.5-inventory-parity.md) | **Current** |
| 4 | [Labels & QR](prd/80.14-ralph-phase-4-labels-qr.md) | Pending |
