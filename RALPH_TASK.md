---
task: Deprecate NiceGUI
test_command: pytest tests/ -v --tb=short && cd frontend && npm run build
browser_validation: false
---

# Task: Deprecate and Remove NiceGUI

Remove NiceGUI code, dependencies, and documentation references. Vue/Quasar is now the sole frontend.

**PRD Reference:** [prd/90.10-deprecate-nicegui.md](prd/90.10-deprecate-nicegui.md)

## Success Criteria

### Code Removal

- [ ] **[1] [CRITICAL]** Delete `app/ui/` directory entirely
  - All 14 Python files removed
  - Test: `ls app/ui/` returns "No such file or directory"

- [ ] **[2] [CRITICAL]** Remove NiceGUI from `app/main.py`
  - Remove NiceGUI imports
  - Remove `ui.run()` or NiceGUI mounting code
  - Remove any NiceGUI-specific middleware
  - Test: `grep -r "nicegui" app/main.py` returns nothing

- [ ] **[3] [CRITICAL]** Remove NiceGUI from dependencies
  - Remove from `requirements.txt`
  - Remove from `pyproject.toml`
  - Test: `grep nicegui requirements.txt` returns nothing

- [ ] **[4] [CORE]** Clean up any remaining NiceGUI imports
  - Check `app/api/routes/me.py` for NiceGUI references
  - Remove any `from nicegui import` statements
  - Test: `grep -r "from nicegui" app/` returns nothing

### Documentation Updates

- [ ] **[5] [CRITICAL]** Update Phase 3 PRD
  - Remove Option A (NiceGUI validation path)
  - Make Option B (Vue/Quasar) the only path
  - Update `browser_url` to `:3335` only

- [ ] **[6] [CORE]** Update architecture PRDs
  - Update `prd/30.10-technical-architecture.md` frontend stack
  - Update `prd/30.13-ui-specification.md` to Vue only
  - Update `prd/40.15-deployment.md` if needed

- [ ] **[7] [CORE]** Update feature PRDs
  - Update `prd/feature-scanner-gun-mode.md` to Vue
  - Update `prd/feature-product-name-search.md` to Vue

- [ ] **[8] [FLEX]** Update project documentation
  - Update `README.md` stack description
  - Add entry to `CHANGELOG.md`
  - Add decision to `prd/91.14-decision-log.md`

---

## Context

- **Deploy Target:** `192.168.200.37` via SSH (root)
- **Install Path:** `/opt/grocyscan/`
- **Port:** 3334 (API), 3335 (Vue frontend)
- Vue/Quasar frontend has full feature parity

## Phase Navigation

| Phase | Document | Status |
|-------|----------|--------|
| 1 | [Foundation](prd/80.11-ralph-phase-1-foundation.md) | Complete |
| 2 | [Inventory](prd/80.12-ralph-phase-2-inventory.md) | Complete |
| 3 | [Device & UI](prd/80.13-ralph-phase-3-device-ui.md) | Complete |
| Maintenance | [Deprecate NiceGUI](prd/90.10-deprecate-nicegui.md) | **Current** |
| 4 | [Labels & QR](prd/80.14-ralph-phase-4-labels-qr.md) | Pending |
