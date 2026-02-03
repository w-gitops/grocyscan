---
name: Homebot PRD Organization
overview: Update ALL existing PRD documents to Homebot branding + Vue/Quasar stack, merge Ralph reference materials, extract chat content into new feature PRDs, and prepare for Ralph Wiggum task execution.
todos:
  - id: update-standards
    content: "Update 00-Standards-of-Development.md: Merge GUARDRAILS.md, GIT_WORKFLOW.md, rename to Homebot"
    status: pending
  - id: update-exec-summary
    content: "Update 01-executive-summary.md: Homebot branding, Vue/Quasar stack, expanded scope"
    status: pending
  - id: update-user-stories
    content: "Update 02-user-stories.md: Add new stories from chat (device, QR, labels, people, etc.)"
    status: pending
  - id: update-functional
    content: "Update 03-functional-requirements.md: Add all FR-xxx from chat, rename to Homebot"
    status: pending
  - id: update-tech-arch
    content: "Update 04-technical-architecture.md: Vue/Quasar frontend, Grocy compat layer, Paperless-ngx"
    status: pending
  - id: update-data-models
    content: "Update 05-data-models.md: Add all new entities from chat (Device, QR, Container, LPN, People, etc.)"
    status: pending
  - id: update-api-spec
    content: "Update 06-api-specification.md: /api (Grocy), /api/v2 (native), all new endpoints"
    status: pending
  - id: update-ui-spec
    content: "Update 07-ui-specification.md: Vue/Quasar components, layouts, label designer"
    status: pending
  - id: update-observability
    content: "Update 08-observability.md: Homebot branding"
    status: pending
  - id: update-installation
    content: "Update 09-installation-operations.md: SSH to .37, Docker Compose stack, shared Postgres"
    status: pending
  - id: update-testing
    content: "Update 10-testing-strategy.md: BrowserMCP integration, Ralph test patterns"
    status: pending
  - id: update-schema
    content: "Update 11-schema-evolution.md: Homebot branding"
    status: pending
  - id: update-security
    content: "Update 12-security.md: Homebot branding"
    status: pending
  - id: update-project-standards
    content: "Update 13-project-standards.md: Homebot branding, Vue/Quasar conventions"
    status: pending
  - id: update-delivery
    content: "Update 14-delivery-plan.md: New 7-phase Ralph execution plan"
    status: pending
  - id: update-appendices
    content: "Update all appendices (A-F): Homebot branding, new API docs"
    status: pending
  - id: create-appendix-g
    content: "Create appendix-g-deployment.md: SSH deployment, Docker Compose, server config"
    status: pending
  - id: update-deploy-scripts
    content: Update scripts/deploy.ps1 and deploy.sh for Homebot + Docker Compose stack
    status: pending
  - id: create-22-integrations
    content: "Create 22-integrations-settings.md: Integrations UI, ports, URL config, CORS"
    status: pending
  # Phase B: Create New Feature PRDs in prd/homebot/
  - id: create-structure
    content: Create prd/homebot/ folder structure, archive chat file
    status: pending
  - id: create-10-device
    content: "Create 10-device-preferences.md: Device registration, prefs, action modes"
    status: pending
  - id: create-11-qr
    content: "Create 11-qr-routing-system.md: QR generation, assignment, routing"
    status: pending
  - id: create-12-labels
    content: "Create 12-label-printing.md: Brother QL, label designer, templates"
    status: pending
  - id: create-13-containers
    content: "Create 13-container-management.md: Containers, nesting, location hierarchy"
    status: pending
  - id: create-14-lpn
    content: "Create 14-lpn-instance-tracking.md: LPN system, FIFO, instance management"
    status: pending
  - id: create-15-people
    content: "Create 15-people-consumption.md: Household people, consumption, routines"
    status: pending
  - id: create-16-recipes
    content: "Create 16-recipes-meal-planning.md: Recipes, meal plans, fulfillment"
    status: pending
  - id: create-17-shopping
    content: "Create 17-shopping-lists.md: Shopping lists, store integration"
    status: pending
  - id: create-18-intelligence
    content: "Create 18-food-intelligence.md: Custom fields, blends, safety"
    status: pending
  - id: create-19-cost
    content: "Create 19-cost-tracking.md: Stores, purchases, DCA, receipts"
    status: pending
  - id: create-20-paperless
    content: "Create 20-paperless-integration.md: Paperless-ngx stack, OCR"
    status: pending
  - id: create-21-returns
    content: "Create 21-return-tracking.md: Return deadlines, state machine"
    status: pending
  - id: create-ralph-overview
    content: "Create 80-ralph-phases.md: Overall phase breakdown, dependencies"
    status: pending
  - id: create-phase-1
    content: "Create 81-phase-1-foundation.md: Core API, models, auth tasks"
    status: pending
  - id: create-phase-2
    content: "Create 82-phase-2-inventory.md: Inventory, locations, containers tasks"
    status: pending
  - id: create-phase-3
    content: "Create 83-phase-3-device-ui.md: Frontend, device prefs tasks"
    status: pending
  - id: create-phase-4
    content: "Create 84-phase-4-labels-qr.md: QR, labels, printing tasks"
    status: pending
  - id: create-phase-5
    content: "Create 85-phase-5-recipes.md: Recipes, meal plans, shopping tasks"
    status: pending
  - id: create-phase-6
    content: "Create 86-phase-6-intelligence.md: Food intel, cost tracking tasks"
    status: pending
  - id: create-phase-7
    content: "Create 87-phase-7-documents.md: Paperless, returns tasks"
    status: pending
isProject: false
---

# Homebot PRD Organization Plan

## Scope

This plan covers FOUR major workstreams:

1. **Update Existing PRDs** - Rebrand all 00-14 + appendices from GrocyScan to Homebot, update tech stack from NiceGUI to Vue/Quasar, **add task sections to each PRD**
2. **Merge Ralph References** - Incorporate GUARDRAILS.md, GIT_WORKFLOW.md into 00-Standards-of-Development.md
3. **Extract New Features** - Create detailed feature PRDs in prd/homebot/ from the design chat
4. **Prepare Ralph Tasks** - Create phase-based task documents for autonomous execution
5. **Deployment Infrastructure** - Update deployment to remote server via SSH, Docker Compose for supporting services

## Deployment Infrastructure

### Target Server

- **Host**: `192.168.200.37`
- **SSH**: `root@192.168.200.37`
- **Install Path**: `/opt/homebot/`
- **Service Name**: `homebot` (systemd)

### Shared PostgreSQL

All services will use the **single existing PostgreSQL server**:

- Homebot main database
- Paperless-ngx database  
- Grafana database (if needed)

### Docker Compose Services (on .37)

Supporting services deployed via Docker Compose:

- **Paperless-ngx** (webserver, worker)
- **Gotenberg** (PDF processing)
- **Tika** (document parsing)
- **Grafana stack** (Grafana, Loki, Prometheus, Tempo)
- **Redis** (caching, queues)

### Deployment Scripts

Update `scripts/deploy.ps1` and `scripts/deploy.sh` to:

- Deploy Homebot application code via SSH
- Deploy Docker Compose stack for supporting services
- Restart services after deployment

### Service Ports (for reverse proxy)


| Service          | Internal Port | Purpose                  |
| ---------------- | ------------- | ------------------------ |
| Homebot API      | 3334          | Main application         |
| Homebot Frontend | 3335          | Vue.js SPA (if separate) |
| Paperless-ngx    | 8001          | Document management UI   |
| Grafana          | 3000          | Observability dashboards |
| Prometheus       | 9090          | Metrics                  |
| Loki             | 3100          | Log aggregation          |


### URL/Domain Configuration

**Environment Variables:**

```
HOMEBOT_BASE_URL=https://homebot.example.com
HOMEBOT_API_URL=https://homebot.example.com/api
PAPERLESS_URL=https://paperless.example.com
```

Used for:

- QR code URL generation (`{HOMEBOT_BASE_URL}/q/{code}`)
- LPN URLs (`{HOMEBOT_BASE_URL}/lpn/{lpn}`)
- Email notification links
- OAuth redirect URLs (future)
- Label printing with QR codes

### CORS Configuration

CORS must be configured for:

- **Grocy clients** (Grocy Android, Home Assistant) accessing `/api/*`
- **External label printers** sending status callbacks
- **Development** (frontend on different port than API)

```python
# Example CORS config
CORS_ALLOWED_ORIGINS = [
    "https://homebot.example.com",
    "https://paperless.example.com",
    # Grocy clients don't typically need CORS (native apps)
]
CORS_ALLOW_CREDENTIALS = True
```

### Integrations Settings UI

The Settings page will include an **Integrations** section showing:

1. **Service Status & Ports**
  - List all services with status (online/offline)
  - Show internal ports for reverse proxy configuration
  - Health check endpoints
2. **URL Configuration**
  - Base URL for link generation
  - API URL (if different)
  - Paperless URL
3. **Integration Configurations**
  - Grocy API (if using external Grocy)
  - Label printers (Brother QL, webhook endpoints)
  - Paperless-ngx connection
  - Home Assistant (future)

## Context

The chat file contains extensive design work for transforming GrocyScan into a standalone home inventory management system. The conversation covered:

- **Grocy API Compatibility** - Hybrid approach with `/api` (Grocy-compatible) and `/api/v2` (native)
- **Frontend Migration** - NiceGUI to Vue.js + Quasar, tablet-first design
- **Device Management** - Per-device preferences, action modes, barcode gun support
- **QR/Label System** - QR routing, Brother QL native printing, label designer
- **Inventory Features** - Containers, LPNs (instance tracking), quantity tracking
- **People & Consumption** - Household members, consumption logging, routines
- **Recipes & Meal Planning** - Grocy-compatible recipes, meal plans, shopping lists
- **Food Intelligence** - Custom fields, proprietary blends, food safety
- **Cost Tracking** - Stores, purchases, DCA, receipt OCR
- **Document Processing** - Paperless-ngx integration, return tracking

---

## Phase A: Update Existing PRD Documents

All existing documents in `prd/` will be updated with:

- **Homebot branding** (replace all GrocyScan/grocyscan references)
- **Vue.js + Quasar stack** (replace NiceGUI references)
- **New architectural decisions** from the design chat

### Standards Document Updates


| Document                                                             | Key Changes                                                                                                                                                                           |
| -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [00-Standards-of-Development.md](prd/00-Standards-of-Development.md) | Merge GUARDRAILS.md (signs concept, types of signs, when to add), merge GIT_WORKFLOW.md (cloud mode, branching), Homebot branding                                                     |
| [01-executive-summary.md](prd/01-executive-summary.md)               | Homebot vision, expanded scope (standalone not just Grocy integration), Vue/Quasar stack                                                                                              |
| [02-user-stories.md](prd/02-user-stories.md)                         | Add US-D01-D06 (devices), US-QR01-QR08 (QR), US-LP01-LP07 (labels), US-P01-P05 (people), US-LPN01-LPN06 (instance tracking)                                                           |
| [03-functional-requirements.md](prd/03-functional-requirements.md)   | Add FR-100 to FR-215 from chat (devices, webhooks, QR, containers, labels)                                                                                                            |
| [04-technical-architecture.md](prd/04-technical-architecture.md)     | Vue.js/Quasar frontend, Grocy compat layer, Paperless-ngx integration, system diagrams                                                                                                |
| [05-data-models.md](prd/05-data-models.md)                           | Add: devices, device_prefs, webhooks, qr_codes, containers, inventory_items (LPN), people, consumption_logs, recipes, meal_plans, shopping_lists, stores, purchases, returnable_items |
| [06-api-specification.md](prd/06-api-specification.md)               | `/api/*` (Grocy compat), `/api/v1/*` (deprecated), `/api/v2/*` (native primary), all new endpoints                                                                                    |
| [07-ui-specification.md](prd/07-ui-specification.md)                 | Vue/Quasar components, tablet/mobile/desktop layouts, label designer wireframes                                                                                                       |
| [08-observability.md](prd/08-observability.md)                       | Homebot branding                                                                                                                                                                      |
| [09-installation-operations.md](prd/09-installation-operations.md)   | SSH deployment to .37, Docker Compose (Paperless, Grafana, Redis), shared Postgres                                                                                                    |
| [10-testing-strategy.md](prd/10-testing-strategy.md)                 | BrowserMCP E2E testing, Ralph test patterns                                                                                                                                           |
| [11-schema-evolution.md](prd/11-schema-evolution.md)                 | Homebot branding                                                                                                                                                                      |
| [12-security.md](prd/12-security.md)                                 | Homebot branding                                                                                                                                                                      |
| [13-project-standards.md](prd/13-project-standards.md)               | Vue/Quasar conventions, TypeScript standards                                                                                                                                          |
| [14-delivery-plan.md](prd/14-delivery-plan.md)                       | 7-phase Ralph execution roadmap                                                                                                                                                       |


### Appendices Updates


| Document                                                                       | Key Changes                                                |
| ------------------------------------------------------------------------------ | ---------------------------------------------------------- |
| [appendix-a-api-documentation.md](prd/appendix-a-api-documentation.md)         | All new API endpoints documented                           |
| [appendix-b-mcp-server.md](prd/appendix-b-mcp-server.md)                       | BrowserMCP testing guidance                                |
| [appendix-c-environment-variables.md](prd/appendix-c-environment-variables.md) | BASE_URL, CORS, Paperless, label printer, shared Postgres  |
| [appendix-d-troubleshooting.md](prd/appendix-d-troubleshooting.md)             | Homebot branding                                           |
| [appendix-e-user-documentation.md](prd/appendix-e-user-documentation.md)       | Homebot branding                                           |
| [appendix-f-n8n-integration.md](prd/appendix-f-n8n-integration.md)             | Homebot branding                                           |
| **NEW: appendix-g-deployment.md**                                              | SSH deployment, Docker Compose stack, server configuration |


### Task Tracking in PRDs

Each updated PRD document will include a **Tasks Summary** section at the end:

```markdown
## Tasks Summary

Tasks derived from this PRD for Ralph execution:

| Task ID | Description | Phase | Priority |
|---------|-------------|-------|----------|
| HB-xxx  | Description | 1-7   | P0/P1/P2 |
```

This ensures all tasks are traceable back to their PRD source and provides a complete task inventory across the entire PRD set.

---

## Phase B: New Feature PRDs in prd/homebot/

Create detailed feature specifications extracted from the design chat:


| Document                      | Content                                         | Chat Lines (approx) |
| ----------------------------- | ----------------------------------------------- | ------------------- |
| `10-device-preferences.md`    | Device registration, preferences, action modes  | 1700-2100           |
| `11-qr-routing-system.md`     | QR generation, assignment, routing, URL scheme  | 1955-1970           |
| `12-label-printing.md`        | Brother QL, label designer, templates, webhooks | 11700-12600         |
| `13-container-management.md`  | Containers, nesting, location hierarchy         | 1970-2000           |
| `14-lpn-instance-tracking.md` | LPN system, FIFO enforcement, mixed inventory   | 7040-7500           |
| `15-people-consumption.md`    | Household people, consumption logging, routines | 6500-7040           |
| `16-recipes-meal-planning.md` | Recipes, meal plans, fulfillment checking       | FR-060-075          |
| `17-shopping-lists.md`        | Shopping lists, store integration               | FR-080-085          |
| `18-food-intelligence.md`     | Custom fields, proprietary blends, food safety  | 9500-9850           |
| `19-cost-tracking.md`         | Stores, purchases, DCA, receipt processing      | 9885-10770          |
| `20-paperless-integration.md` | Paperless-ngx stack, document flow, OCR         | 10775-10920         |
| `21-return-tracking.md`       | Return deadlines, state machine, policies       | 10960-11350         |
| `22-integrations-settings.md` | Integrations UI, service ports, URL/CORS config | New                 |


---

## Phase C: Ralph Execution Documents in prd/homebot/


| Document                     | Content                                                   |
| ---------------------------- | --------------------------------------------------------- |
| `80-ralph-phases.md`         | Overall phase breakdown, dependencies, execution order    |
| `81-phase-1-foundation.md`   | PostgreSQL schema, FastAPI structure, core models, auth   |
| `82-phase-2-inventory.md`    | Inventory, LPN, locations, containers, Grocy stock compat |
| `83-phase-3-device-ui.md`    | Vue/Quasar setup, device prefs, layouts, scanner          |
| `84-phase-4-labels-qr.md`    | QR routing, Brother QL, label designer                    |
| `85-phase-5-recipes.md`      | Recipes, meal plans, shopping lists, Grocy compat         |
| `86-phase-6-intelligence.md` | Userfields, food safety, cost tracking                    |
| `87-phase-7-documents.md`    | Paperless-ngx, receipt OCR, return tracking               |


---

## Ralph Reference Materials to Merge

The following content from `ralph-wiggum-cursor/` will be merged into [00-Standards-of-Development.md](prd/00-Standards-of-Development.md):

### From GUARDRAILS.md (references/GUARDRAILS.md)

- **Signs metaphor** explanation ("Ralph is very good at making playgrounds...")
- **Anatomy of a sign** template
- **Types of signs**: Preventive, Corrective, Process, Architecture
- **When to add signs** criteria
- **Sign lifecycle**: Creation, Refinement, Retirement
- **Example signs library**: Security, Error Handling, Testing, Code Quality

### From GIT_WORKFLOW.md (assets/GIT_WORKFLOW.md)

- **Cloud Mode workflow** (main branch vs ralph-iteration-N branches)
- **Handoff to Cloud Agent** process
- **Merging back to main** (squash merge pattern)
- **Branch cleanup** procedures
- **Workflow diagram**

### From SKILL.md

- Any additional context not already in standards doc

---

## Implementation Phases for Ralph

### Phase 1: Foundation (Priority: P0)

- PostgreSQL database schema
- FastAPI project structure with `/api/v2/*` routes
- Core models: Product, Location, QuantityUnit, ProductGroup
- Authentication system
- Grocy `/api/system/info` endpoint

### Phase 2: Core Inventory (Priority: P0)

- Inventory model with LPN support
- Stock add/consume/transfer operations
- Container model and nesting
- Location hierarchy
- Grocy `/api/stock/*` compatibility endpoints

### Phase 3: Device & Frontend (Priority: P0)

- Vue.js + Quasar project setup
- Device registration and preferences API
- Responsive layouts (tablet/mobile/desktop)
- Action mode system
- Scanner integration (QuaggaJS, barcode gun)

### Phase 4: Labels & QR (Priority: P0)

- QR code generation and routing API
- Brother QL printing service
- Label template system
- Label designer UI
- Webhook outbound for printing

### Phase 5: Recipes & Planning (Priority: P1)

- Recipe model and CRUD
- Ingredient linking
- Recipe fulfillment calculation
- Meal plan system
- Shopping list generation
- Grocy recipes compatibility

### Phase 6: Food Intelligence (Priority: P2)

- Userfield (custom field) system
- Ingredient analysis engine
- Food safety rules
- Processing concern flagging
- Quality scoring

### Phase 7: Documents & Returns (Priority: P2)

- Paperless-ngx Docker integration
- Receipt processing pipeline
- Store and purchase tracking
- DCA calculation
- Return deadline tracking

## Key Files to Extract From

Source: `chat-grocy API Compatibility Strategy.txt`


| Topic                      | Approximate Lines |
| -------------------------- | ----------------- |
| API compatibility PRD      | 300-700           |
| Device preferences         | 1700-2100         |
| QR routing                 | 1955-1970         |
| Containers                 | 1970-2000         |
| Vue.js/Quasar architecture | 5000-5500         |
| ERD diagrams               | 3280-3450         |
| People/consumption         | 6500-7040         |
| LPN system                 | 7040-7500         |
| Food intelligence          | 9500-9850         |
| Food costing               | 9885-10000        |
| Receipt processing         | 10580-10770       |
| Paperless integration      | 10775-10920       |
| Return tracking            | 10960-11350       |
| Label printing             | 11700-12600       |
| Ralph integration          | 11355-11600       |


## Task Format for Ralph

Each phase document will contain tasks in Ralph-compatible format:

```markdown
---
task: [Phase description]
completion_criteria:
  - [Criterion with checkbox]
test_command: pytest tests/ -v
browser_validation: true
---

## Criteria

- [ ] 1. [First criterion]
- [ ] 2. [Second criterion]
```

## Branding & Rename Strategy

### Text Replacements (across all documents)


| Find                 | Replace With       |
| -------------------- | ------------------ |
| `grocyscan`          | `homebot`          |
| `GrocyScan`          | `Homebot`          |
| `grocyscan.app`      | `homebot.app`      |
| `grocyscan.io`       | `homebot.io`       |
| `GROCYSCAN_`         | `HOMEBOT_`         |
| `GrocyScanException` | `HomebotException` |


### Scope Changes

The product is evolving from:

- **Was**: GrocyScan - A barcode scanner that integrates with Grocy
- **Now**: Homebot - A standalone home inventory management system with optional Grocy compatibility

### Key Messaging Updates

- **Tagline**: "Your home, organized" (or similar)
- **Purpose**: Full home inventory, meal planning, cost tracking - not just a Grocy helper
- **Grocy**: Now a compatibility layer, not the core dependency

---

## Execution Order

1. **First**: Update 00-Standards-of-Development.md (merge Ralph refs, branding)
2. **Then**: Update remaining core docs (01-14) with branding + tech stack
3. **Then**: Create new feature PRDs in prd/homebot/ (10-21)
4. **Then**: Create Ralph phase task docs (80-87)
5. **Finally**: Archive the original chat file to prd/archive/

