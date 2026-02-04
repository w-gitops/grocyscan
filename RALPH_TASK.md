---
task: Homebot Phase 3 - Device & UI
test_command: pytest tests/phase3/ tests/phase2/ tests/phase1/ -v --tb=short
browser_validation: false
---

# Task: Homebot Phase 3 - Device & UI

Device registration, preferences, and UI (Vue/Quasar or NiceGUI validation).

**PRD Reference:** [prd/80.13-ralph-phase-3-device-ui.md](prd/80.13-ralph-phase-3-device-ui.md)

## Success Criteria

### Frontend Scaffold

- [ ] **[1]** Vue 3 + Quasar project initialized (Option B) or use NiceGUI (Option A)
- [ ] **[2]** Pinia store configured (auth, device)
- [ ] **[3]** Router with auth guards

### Device Management

- [x] **[4]** Device registration on first visit <!-- POST /api/v2/devices -->
- [x] **[5]** Device preferences stored <!-- PATCH /api/v2/devices/me -->
- [x] **[6]** Device fingerprinting <!-- X-Device-ID, same fingerprint = same device -->

### Scanning Interface

- [ ] **[7]** Camera barcode scanner works
- [x] **[8]** Action mode selection
- [x] **[9]** Quick actions after scan

### Product Views

- [ ] **[10]** Product list with search
- [ ] **[11]** Product detail view
- [ ] **[12]** PWA installable

---

## Context

- **Deploy Target:** `192.168.200.37` via SSH (root)
- **Install Path:** `/opt/grocyscan/`
- **Port:** 3334 (API), 3335 (Vue target)
- **Option A:** Validate with existing NiceGUI at :3334 first.
- **Option B:** Build Vue/Quasar frontend at :3335.

## Technical Notes

- Migration 0006: homebot.devices (fingerprint, default_location_id, default_action, preferences).
- v2 API: POST /api/v2/devices (register), GET/PATCH /api/v2/devices/me (X-Device-ID required for me).

## Phase Navigation

| Phase | Document | Status |
|-------|----------|--------|
| 1 | [Foundation](prd/80.11-ralph-phase-1-foundation.md) | Complete |
| 2 | [Inventory](prd/80.12-ralph-phase-2-inventory.md) | Complete |
| 3 | [Device & UI](prd/80.13-ralph-phase-3-device-ui.md) | **Current** |
| 4 | [Labels & QR](prd/80.14-ralph-phase-4-labels-qr.md) | Pending |
| 5 | [Recipes](prd/80.15-ralph-phase-5-recipes.md) | Pending |
| 6 | [Intelligence](prd/80.16-ralph-phase-6-intelligence.md) | Pending |
| 7 | [Documents](prd/80.17-ralph-phase-7-documents.md) | Pending |
