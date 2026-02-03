---
task: Homebot Phase 1 - Foundation
test_command: pytest tests/phase1/ -v --tb=short
browser_validation: false
---

# Task: Homebot Phase 1 - Foundation

Build the core infrastructure for Homebot: PostgreSQL with multi-tenant RLS, FastAPI application skeleton, and JWT/API key authentication.

**PRD Reference:** [prd/80.11-ralph-phase-1-foundation.md](prd/80.11-ralph-phase-1-foundation.md)

## Success Criteria

### Database & Schema

- [x] PostgreSQL database created with `homebot` schema <!-- group: 1 -->
- [x] Tenants table with RLS enabled <!-- group: 1 -->
- [x] Users table with tenant membership <!-- group: 1 -->
- [x] Alembic migrations configured <!-- group: 1 -->

### Authentication

- [x] JWT authentication working <!-- group: 2 -->
- [x] API key authentication for service accounts <!-- group: 2 -->
- [x] Password hashing with bcrypt <!-- group: 2 -->

### API Structure

- [x] FastAPI app starts without errors <!-- group: 3 -->
- [x] OpenAPI spec generated at `/docs` <!-- group: 3 -->
- [x] Basic logging configured <!-- group: 3 -->

---

## Context

- **Deploy Target:** `192.168.200.37` via SSH (root)
- **Install Path:** `/opt/homebot/`
- **Service:** `homebot` (systemd)
- **Port:** 3334

## Technical Notes

See [prd/80.11-ralph-phase-1-foundation.md](prd/80.11-ralph-phase-1-foundation.md) for:
- Detailed acceptance criteria with test commands
- Files to create/modify
- RLS setup patterns
- Environment variables

## Environment Variables

```bash
DATABASE_URL=postgresql://homebot:password@localhost:5432/homebot
SECRET_KEY=your-secret-key-here
HOMEBOT_DEBUG=false
```

## Phase Navigation

| Phase | Document | Status |
|-------|----------|--------|
| 1 | [Foundation](prd/80.11-ralph-phase-1-foundation.md) | **Current** |
| 2 | [Inventory](prd/80.12-ralph-phase-2-inventory.md) | Pending |
| 3 | [Device UI](prd/80.13-ralph-phase-3-device-ui.md) | Pending |
| 4 | [Labels & QR](prd/80.14-ralph-phase-4-labels-qr.md) | Pending |
| 5 | [Recipes](prd/80.15-ralph-phase-5-recipes.md) | Pending |
| 6 | [Intelligence](prd/80.16-ralph-phase-6-intelligence.md) | Pending |
| 7 | [Documents](prd/80.17-ralph-phase-7-documents.md) | Pending |
