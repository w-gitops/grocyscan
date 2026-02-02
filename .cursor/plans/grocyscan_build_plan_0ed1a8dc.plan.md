---
name: GrocyScan Build Plan
overview: Build GrocyScan - a barcode scanning app for grocery inventory management - following the Ralph Wiggum autonomous development methodology with iterative, criterion-based development across 6 phases.
todos:
  - id: phase-1
    content: "Phase 1: Foundation - Project scaffolding, database models, auth, Docker setup"
    status: pending
  - id: phase-2
    content: "Phase 2: Core Scanning - Barcode validation, OpenFoodFacts, Grocy client, scan UI"
    status: pending
  - id: phase-3
    content: "Phase 3: Enhanced Lookup - Multi-provider lookup, LLM optimization, settings UI"
    status: pending
  - id: phase-4
    content: "Phase 4: Full Features - Locations, date picker, job queue, offline support"
    status: pending
  - id: phase-5
    content: "Phase 5: Observability - OpenTelemetry, Prometheus, Grafana, log viewer"
    status: pending
  - id: phase-6
    content: "Phase 6: Production Readiness - Test coverage, docs, security audit, v1.0.0 release"
    status: pending
isProject: false
---

# GrocyScan Implementation Plan

This plan follows the **Ralph Wiggum** autonomous development methodology from [00-Standards-of-Development.md](C:\git\cursor-command\templates\prd\00-Standards-of-Development.md). All development will be tracked via `RALPH_TASK.md` with atomic, testable criteria committed incrementally.

---

## Project Structure

Following the standard layout from Section 0.14:

```
grocyscan/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI + NiceGUI entry
│   ├── config.py                  # Pydantic settings
│   │
│   ├── api/                       # REST endpoints
│   │   ├── routes/
│   │   │   ├── scan.py
│   │   │   ├── products.py
│   │   │   ├── locations.py
│   │   │   ├── jobs.py
│   │   │   ├── settings.py
│   │   │   ├── logs.py
│   │   │   └── auth.py
│   │   └── deps.py                # Dependency injection
│   │
│   ├── ui/                        # NiceGUI pages
│   │   ├── pages/
│   │   │   ├── scan.py
│   │   │   ├── review.py
│   │   │   ├── products.py
│   │   │   ├── locations.py
│   │   │   ├── jobs.py
│   │   │   ├── logs.py
│   │   │   ├── settings.py
│   │   │   └── login.py
│   │   └── components/
│   │       ├── scanner.py
│   │       ├── date_picker.py
│   │       ├── product_grid.py
│   │       └── detail_popup.py
│   │
│   ├── services/                  # Business logic
│   │   ├── lookup/
│   │   │   ├── manager.py
│   │   │   ├── openfoodfacts.py
│   │   │   ├── goupc.py
│   │   │   ├── upcitemdb.py
│   │   │   ├── brave.py
│   │   │   └── federation.py
│   │   ├── llm/
│   │   │   ├── optimizer.py
│   │   │   ├── merger.py
│   │   │   └── client.py
│   │   ├── grocy/
│   │   │   ├── client.py
│   │   │   └── sync.py
│   │   ├── queue/
│   │   │   ├── manager.py
│   │   │   └── workers.py
│   │   └── auth.py
│   │
│   ├── db/
│   │   ├── database.py
│   │   ├── models.py
│   │   └── crud/
│   │
│   ├── core/
│   │   ├── logging.py
│   │   ├── telemetry.py
│   │   └── exceptions.py
│   │
│   └── schemas/                   # Pydantic models
│
├── migrations/                    # Alembic
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── database/
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── scripts/
├── .ralph/
│   ├── progress.md
│   ├── guardrails.md
│   └── screenshots/
│
├── RALPH_TASK.md
├── pyproject.toml
├── requirements.txt
└── .env.example
```

---

## Phase 1: Foundation

**Goal**: Running application skeleton with authentication

### RALPH_TASK.md Criteria

1. Project scaffolding with `pyproject.toml` and dependencies
2. PostgreSQL database models (users, products, barcodes, locations, stock_entries, lookup_cache, job_queue, scan_history, settings)
3. Alembic migration setup with initial schema
4. FastAPI application shell with health endpoint
5. Pydantic settings configuration (`config.py` with `SecretStr`)
6. Structlog JSON logging setup
7. NiceGUI application shell with routing
8. Authentication service (bcrypt password hashing)
9. Login page UI (simple username/password)
10. Session management middleware (24h idle, 7d absolute)
11. Docker Compose setup (postgres, redis, app)
12. Basic test fixtures (`conftest.py`)

### Key Implementation Details

- Use `pydantic-settings` with `.env` file support
- PostgreSQL 17, Redis for caching
- All tables include `user_id` for future multi-user
- Session cookies: `HttpOnly`, `Secure`, `SameSite=Strict`

---

## Phase 2: Core Scanning

**Goal**: Basic scan-to-add workflow with OpenFoodFacts

### RALPH_TASK.md Criteria

1. Barcode validation utility (EAN-13, UPC-A, UPC-E, EAN-8)
2. OpenFoodFacts provider implementation
3. Lookup cache service (Redis, 30-day TTL)
4. Basic Grocy client (product CRUD, stock management)
5. `POST /api/scan` endpoint
6. `POST /api/scan/{id}/confirm` endpoint
7. Scan page UI (input field, feedback display)
8. Review popup component (70% width modal)
9. Product detail editing in review
10. Location barcode parsing (`LOC-{AREA}-{NUMBER}`)
11. USB/Bluetooth scanner input handling (kiosk mode)
12. Audio/visual feedback on successful scan
13. Integration test: full scan-to-add flow
14. Browser validation: scan page works on mobile

---

## Phase 3: Enhanced Lookup

**Goal**: Multi-provider lookup with LLM optimization

### RALPH_TASK.md Criteria

1. go-upc provider implementation
2. UPCItemDB provider implementation
3. Brave Search provider implementation
4. Barcode Buddy Federation provider
5. Lookup manager (sequential strategy)
6. Lookup manager (parallel strategy with LLM selection)
7. Provider priority configuration
8. LLM client wrapper (LiteLLM)
9. LLM optimizer (name cleaning, category inference)
10. LLM merger (multi-source data reconciliation)
11. LLM failure handling (non-blocking, queued retry)
12. Product image download and local storage
13. Settings page: Lookup provider configuration (drag-and-drop)
14. Settings page: LLM endpoint configuration

---

## Phase 4: Full Features

**Goal**: Complete feature set including offline support

### RALPH_TASK.md Criteria

1. Location management API endpoints
2. Locations page UI (code generation, Grocy sync)
3. Touch-friendly date picker component
4. Date picker quick-select buttons (TODAY, +3D, +1W, +2W, +1M, +3M, NONE)
5. Job queue database operations
6. Background task workers
7. Job queue API endpoints
8. Job queue page UI (AG Grid)
9. Offline detection service
10. IndexedDB local queue (frontend)
11. SQLite backup queue (server fallback)
12. Background sync on connectivity restore
13. Products page UI (AG Grid, search, pagination)
14. Product search by name (non-barcode)
15. Fuzzy matching for existing products (90% threshold)
16. Create product without adding quantity

---

## Phase 5: Observability and Polish

**Goal**: Full observability stack and admin tools

### RALPH_TASK.md Criteria

1. OpenTelemetry instrumentation setup
2. Trace context injection in logs
3. Prometheus metrics endpoint (`/metrics`)
4. Custom metrics (scan duration, lookup success rate, queue size)
5. Grafana dashboard configuration
6. Log viewer API endpoint
7. Log viewer page UI (filter, search, copy)
8. Settings page: Grocy configuration with connection test
9. Settings page: Scanning options (auto-add, beep sounds)
10. Dark mode support
11. Mobile responsive polish (bottom nav)
12. Kiosk mode option

---

## Phase 6: Production Readiness

**Goal**: Production-ready v1.0.0 release

### RALPH_TASK.md Criteria

1. Unit test coverage >80%
2. Integration test: all API endpoints
3. Database migration tests
4. Browser tests: critical user flows
5. Security audit (rate limiting, input validation)
6. Performance optimization (query optimization, caching)
7. Install script (bare metal Debian LXC)
8. Documentation: README with setup instructions
9. Documentation: API reference (OpenAPI export)
10. Environment variable documentation
11. Troubleshooting guide
12. Release v1.0.0 tag

---

## Quality Standards Checklist

Per Section 0.2 of the Standards:

- **Type Safety**: All code passes `mypy` strict mode
- **Linting**: `ruff` with no errors
- **Formatting**: `black` auto-format
- **Documentation**: Docstrings for all public APIs
- **Testing**: >80% unit coverage, critical path integration tests
- **Logging**: Structured JSON with trace correlation
- **Security**: Secrets in `SecretStr`, rate limiting, input validation

---

## Tech Stack Summary


| Layer      | Technology                         |
| ---------- | ---------------------------------- |
| Backend    | Python 3.11+, FastAPI              |
| Frontend   | NiceGUI (Python web UI)            |
| Database   | PostgreSQL 17, SQLAlchemy, Alembic |
| Cache      | Redis                              |
| LLM        | LiteLLM (OpenAI-compatible)        |
| Logging    | structlog (JSON)                   |
| Metrics    | Prometheus                         |
| Tracing    | OpenTelemetry → Tempo              |
| Testing    | pytest                             |
| Deployment | Docker Compose                     |


---

## Development Workflow

Each phase will:

1. Create `RALPH_TASK.md` with numbered success criteria
2. Work through criteria one at a time
3. Commit each completed criterion with `ralph: [N] Description`
4. Update `.ralph/progress.md` after each session
5. Add failures to `.ralph/guardrails.md`
6. Push after every 3-5 commits

---

## First Task: Initialize Phase 1

Begin with project scaffolding:

```yaml
---
task: Phase 1 - Foundation Setup
test_command: "pytest tests/ -v"
browser_validation: true
base_url: "http://localhost:8000"
---

## Success Criteria

1. [ ] Create project scaffolding with pyproject.toml and dependencies
2. [ ] Implement PostgreSQL database models (9 tables)
3. [ ] Set up Alembic with initial migration
4. [ ] Create FastAPI app shell with /health endpoint
5. [ ] Configure Pydantic settings with SecretStr
6. [ ] Set up structlog JSON logging
7. [ ] Create NiceGUI application shell with routing
8. [ ] Implement authentication service (bcrypt)
9. [ ] Build login page UI
10. [ ] Add session management middleware
11. [ ] Create Docker Compose configuration
12. [ ] Set up test fixtures in conftest.py
```

