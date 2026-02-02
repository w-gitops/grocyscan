# 4. Technical Architecture

## 4.1 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   CLIENTS                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ Mobile PWA  │  │   Tablet    │  │   Desktop   │  │  USB/Bluetooth Scanner  │ │
│  │  (Camera)   │  │ (Touchscreen│  │  (Webcam)   │  │   (Keyboard Emulation)  │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └────────────┬────────────┘ │
└─────────┼────────────────┼────────────────┼──────────────────────┼──────────────┘
          │                │                │                      │
          └────────────────┴────────────────┴──────────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Reverse Proxy     │
                         │  (Caddy/Traefik)    │
                         │   TLS Termination   │
                         └──────────┬──────────┘
                                    │ HTTP :3334
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            GROCYSCAN APPLICATION                                 │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                         NiceGUI Frontend Layer                             │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │ │
│  │  │  Scan    │ │  Review  │ │ Products │ │ Settings │ │    Job Queue     │  │ │
│  │  │  Page    │ │  Page    │ │  Search  │ │  Page    │ │      Page        │  │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────────────┘  │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │ │
│  │  │ Location │ │   Date   │ │   Log    │ │  Login   │ │     AG Grid      │  │ │
│  │  │ Scanner  │ │  Picker  │ │  Viewer  │ │  Page    │ │   Components     │  │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                           │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                         FastAPI Backend Layer                              │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────────────┐ │ │
│  │  │   /api/scan  │ │/api/products │ │/api/locations│ │   /api/settings    │ │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └────────────────────┘ │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────────────┐ │ │
│  │  │  /api/jobs   │ │  /api/logs   │ │  /api/auth   │ │     /metrics       │ │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                           │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                          Services Layer                                    │ │
│  │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────────────┐   │ │
│  │  │  Lookup Service │ │   LLM Service   │ │      Grocy Service          │   │ │
│  │  │  ┌───────────┐  │ │  ┌───────────┐  │ │  ┌───────────────────────┐  │   │ │
│  │  │  │OpenFood   │  │ │  │  LiteLLM  │  │ │  │   Product CRUD        │  │   │ │
│  │  │  │Facts      │  │ │  │  Router   │  │ │  │   Stock Management    │  │   │ │
│  │  │  ├───────────┤  │ │  ├───────────┤  │ │  │   Location Sync       │  │   │ │
│  │  │  │ go-upc    │  │ │  │  OpenAI   │  │ │  └───────────────────────┘  │   │ │
│  │  │  ├───────────┤  │ │  │  Anthropic│  │ └─────────────────────────────┘   │ │
│  │  │  │UPCItemDB  │  │ │  │  Ollama   │  │ ┌─────────────────────────────┐   │ │
│  │  │  ├───────────┤  │ │  │  Generic  │  │ │      Queue Service          │   │ │
│  │  │  │Brave      │  │ │  └───────────┘  │ │  ┌───────────────────────┐  │   │ │
│  │  │  │Search     │  │ └─────────────────┘ │  │   Offline Sync        │  │   │ │
│  │  │  ├───────────┤  │                     │  │   LLM Retry Queue     │  │   │ │
│  │  │  │Federation │  │                     │  │   Background Tasks    │  │   │ │
│  │  │  └───────────┘  │                     │  └───────────────────────┘  │   │ │
│  │  └─────────────────┘                     └─────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                           │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                       Data & Cache Layer                                   │ │
│  │  ┌─────────────────────────────┐  ┌─────────────────────────────────────┐  │ │
│  │  │       PostgreSQL 17         │  │              Redis                  │  │ │
│  │  │  ┌───────────────────────┐  │  │  ┌───────────────────────────────┐  │  │ │
│  │  │  │ users (multi-user)    │  │  │  │  Lookup Cache (TTL: 30d)     │  │  │ │
│  │  │  │ products              │  │  │  │  LLM Response Cache          │  │  │ │
│  │  │  │ barcodes              │  │  │  │  Session Data                │  │  │ │
│  │  │  │ stock_entries         │  │  │  │  Rate Limit Counters         │  │  │ │
│  │  │  │ locations             │  │  │  └───────────────────────────────┘  │  │ │
│  │  │  │ job_queue             │  │  └─────────────────────────────────────┘  │ │
│  │  │  │ scan_history          │  │                                           │ │
│  │  │  │ settings              │  │                                           │ │
│  │  │  └───────────────────────┘  │                                           │ │
│  │  └─────────────────────────────┘                                           │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│    Grocy Server     │   │   LLM Providers     │   │  Lookup Providers   │
│  (Internal API URL) │   │  ┌───────────────┐  │   │  ┌───────────────┐  │
│                     │   │  │ OpenAI API    │  │   │  │OpenFoodFacts  │  │
│  Products, Stock,   │   │  │ Anthropic API │  │   │  │go-upc.com     │  │
│  Locations, etc.    │   │  │ Ollama (local)│  │   │  │UPCItemDB      │  │
│                     │   │  │ OpenRouter    │  │   │  │Brave Search   │  │
└─────────────────────┘   │  └───────────────┘  │   │  │BB Federation  │  │
                          └─────────────────────┘   │  └───────────────┘  │
                                                    └─────────────────────┘
```

## 4.2 Directory Structure

```
grocyscan/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI + NiceGUI application entry
│   ├── config.py                  # Settings from environment variables
│   │
│   ├── api/                       # FastAPI REST endpoints
│   │   ├── __init__.py
│   │   ├── router.py              # Main API router
│   │   ├── scan.py                # POST /api/scan
│   │   ├── products.py            # Product CRUD endpoints
│   │   ├── locations.py           # Location endpoints
│   │   ├── jobs.py                # Job queue endpoints
│   │   ├── settings.py            # Settings endpoints
│   │   ├── logs.py                # Log retrieval endpoints
│   │   └── auth.py                # Authentication endpoints
│   │
│   ├── ui/                        # NiceGUI pages and components
│   │   ├── __init__.py
│   │   ├── pages/
│   │   │   ├── __init__.py
│   │   │   ├── scan.py            # Main scanning page
│   │   │   ├── review.py          # Product review before add
│   │   │   ├── products.py        # Product search/management
│   │   │   ├── locations.py       # Location management
│   │   │   ├── jobs.py            # Job queue viewer
│   │   │   ├── logs.py            # Log viewer
│   │   │   ├── settings.py        # Settings page
│   │   │   └── login.py           # Login page
│   │   │
│   │   └── components/
│   │       ├── __init__.py
│   │       ├── barcode_scanner.py # Camera/input scanner component
│   │       ├── date_picker.py     # Touch-friendly date picker
│   │       ├── product_grid.py    # AG Grid product table
│   │       ├── job_queue.py       # Job queue AG Grid
│   │       ├── log_viewer.py      # Log viewer component
│   │       └── detail_popup.py    # 70% width detail popup
│   │
│   ├── services/                  # Business logic layer
│   │   ├── __init__.py
│   │   ├── lookup/
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # Provider interface
│   │   │   ├── manager.py         # Lookup orchestration
│   │   │   ├── openfoodfacts.py
│   │   │   ├── goupc.py
│   │   │   ├── upcitemdb.py
│   │   │   ├── brave.py
│   │   │   └── federation.py
│   │   │
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── optimizer.py       # Product data optimization
│   │   │   ├── merger.py          # Multi-source data merging
│   │   │   └── client.py          # LiteLLM client wrapper
│   │   │
│   │   ├── grocy/
│   │   │   ├── __init__.py
│   │   │   ├── client.py          # Grocy API client
│   │   │   ├── products.py        # Product operations
│   │   │   ├── stock.py           # Stock operations
│   │   │   └── locations.py       # Location operations
│   │   │
│   │   ├── queue/
│   │   │   ├── __init__.py
│   │   │   ├── manager.py         # Job queue management
│   │   │   ├── workers.py         # Background task workers
│   │   │   └── sync.py            # Offline sync logic
│   │   │
│   │   └── auth/
│   │       ├── __init__.py
│   │       ├── service.py         # Authentication logic
│   │       └── session.py         # Session management
│   │
│   ├── db/                        # Database layer
│   │   ├── __init__.py
│   │   ├── database.py            # SQLAlchemy engine/session
│   │   ├── models.py              # SQLAlchemy ORM models
│   │   └── crud/
│   │       ├── __init__.py
│   │       ├── products.py
│   │       ├── barcodes.py
│   │       ├── stock.py
│   │       ├── locations.py
│   │       ├── jobs.py
│   │       ├── users.py
│   │       └── settings.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── logging.py             # Structlog configuration
│   │   ├── telemetry.py           # OpenTelemetry setup
│   │   ├── metrics.py             # Prometheus metrics
│   │   └── exceptions.py          # Custom exceptions
│   │
│   └── schemas/                   # Pydantic models
│       ├── __init__.py
│       ├── scan.py
│       ├── product.py
│       ├── location.py
│       ├── job.py
│       ├── settings.py
│       └── user.py
│
├── migrations/                    # Alembic migrations
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
│       └── 001_initial_schema.py
│
├── tests/
│   ├── conftest.py                # Shared fixtures
│   ├── unit/
│   │   ├── test_lookup_providers.py
│   │   ├── test_llm_optimizer.py
│   │   ├── test_barcode_validator.py
│   │   └── test_grocy_client.py
│   ├── integration/
│   │   ├── test_scan_flow.py
│   │   ├── test_api_endpoints.py
│   │   └── test_grocy_integration.py
│   └── database/
│       ├── test_migrations.py
│       └── test_crud_operations.py
│
├── docs/
│   └── standards/                 # Project standards
│       ├── README.md
│       ├── VERSIONING.md
│       ├── CHANGELOG.md
│       ├── COMMIT_MESSAGES.md
│       ├── LOGGING.md
│       ├── TESTING.md
│       ├── DATABASE.md
│       ├── API.md
│       ├── UI_COMPONENTS.md
│       ├── PRD_TEMPLATE.md
│       ├── USER_STORY_TEMPLATE.md
│       └── CODE_STYLE.md
│
├── scripts/
│   ├── install.sh                 # curl-compatible install script
│   ├── upgrade.sh                 # Git-based upgrade script
│   ├── start.sh
│   ├── stop.sh
│   └── restart.sh
│
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml         # Production stack
│   ├── docker-compose.dev.yml     # Development overrides
│   └── docker-compose.observability.yml  # Observability stack
│
├── .env.example                   # Environment variable template
├── pyproject.toml                 # Python project configuration
├── requirements.txt               # Python dependencies
├── CHANGELOG.md
├── LICENSE
└── README.md
```

## 4.3 Multi-User Architecture Pre-Design

While MVP implements single-user mode, the architecture is designed for future multi-user expansion.

### 4.3.1 Authentication Strategy

FastAPI supports multiple security schemes including OAuth2 with JWT tokens. The recommended approach is a 3-tier design pattern with OAuth2 Password authentication flow using Bearer and JSON Web Tokens.

```python
# Future multi-user authentication pattern
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Validate JWT token
    # Return user object
    pass
```

### 4.3.2 NiceGUI Session Isolation

NiceGUI provides server-side storage associated with unique identifiers via browser session cookies. Each user's storage is accessible across all their browser tabs. The `@ui.page` decorator ensures each user accessing a route sees a new instance of the page.

```python
from nicegui import ui, app

@ui.page('/scan')
def scan_page():
    # Each user gets their own instance
    user_id = app.storage.user.get('id')
    # User-specific data and UI state
```

### 4.3.3 Database Multi-Tenancy

For future multi-user support, all data tables include a `user_id` column. The recommended approach is multi-tenant with all data together plus an account key on root tables. PostgreSQL Row-Level Security (RLS) can be added for secure data isolation between tenants.

```python
# All models include user_id for future multi-tenancy
class Product(Base):
    __tablename__ = "products"
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"), index=True)  # Multi-tenant ready
    name = Column(String, nullable=False)
    # ... other fields
```

---

## Navigation

- **Previous:** [Functional Requirements](03-functional-requirements.md)
- **Next:** [Data Models](05-data-models.md)
- **Back to:** [README](README.md)
