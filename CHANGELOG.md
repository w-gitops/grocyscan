# Changelog

All notable changes to GrocyScan will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.3-alpha] - 2026-02-02

### Added

- **Logs Page** - Full log viewer with API and UI
  - API reads from configured `LOG_FILE` (last 500 lines), strips ANSI escape codes, returns `log_file` path
  - `POST /api/logs/clear` truncates log file (with auth)
  - UI: fetch on load, Refresh / Copy / Clear (with confirmation), Level and Search filters
  - Terminal-style dark panel with monospace font and scrollable content
  - Level pill badges (DEBUG, INFO, WARNING, ERROR, CRITICAL) with timestamp-first layout; padded `[level]` brackets stripped from display
  - Restart hint and log file path; note about "Request is not set" in logs

### Fixed

- **NiceGUI "Request is not set"** - Monkey-patch `prune_user_storage` to skip clients without request set (avoids RuntimeError at startup or during disconnect when using `storage_secret`)

## [0.3.2-alpha] - 2026-02-02

### Added

- **Locations Page** - Full implementation fetching and displaying locations from Grocy
  - Shows sync status with location count
  - Displays location cards with freezer indicators
  - "Sync Now" button to refresh from Grocy

- **Products Page** - Full implementation fetching and displaying products from Grocy
  - Search/filter functionality
  - Displays product list with name, description, location, and ID
  - Refresh button to reload from Grocy

- **Dynamic Version Display** - Version now reads from `pyproject.toml` (single source of truth)

### Fixed

- **Grocy Client Settings** - Now reads settings dynamically from `settings_service` instead of static environment variables (hot-reload support)
- **Grocy Product Creation** - Removed unsupported `qu_factor_purchase_to_stock` field for Grocy 4.x compatibility
- **Review Popup Async** - `_handle_confirm` now properly awaits async callbacks (fixes Recent Scans not updating)
- **Products Page Null Safety** - Fixed `'NoneType' object is not subscriptable` error for products with null descriptions

## [0.3.1-alpha] - 2026-02-02

### Added

- **Mobile Camera Scanner Improvements**
  - Dynamic html5-qrcode library loading with status feedback
  - Torch/flash toggle for low-light scanning
  - Automatic 3x zoom on supported devices for better focus distance
  - Mobile-optimized scan box aspect ratio (taller for UPC barcodes)
  - Prioritized UPC/EAN barcode format detection

### Fixed

- **Barcode Validation** - Corrected checksum calculation for UPC-A and EAN-13 barcodes
  - Fixed weighting pattern that was preventing valid barcodes from being recognized
- **Camera Scanner** - Fixed "Initializing camera..." stuck state on mobile and desktop
- **UI Components** - Fixed `ui.input` icon parameter compatibility in Products and Logs pages
- **Async Callbacks** - Fixed slot context errors when handling barcode scan results
- **Touch Detection** - Fixed `has_touch` attribute error in review popup

## [0.3.0-alpha] - 2026-02-02

### Added

- **Dynamic LLM Model Selection** - Fetch available models from LLM provider API
  - New endpoint `GET /api/settings/llm/models` returns available models
  - Supports OpenAI, Ollama, Anthropic, and generic OpenAI-compatible endpoints
  - UI dropdown with refresh button to fetch models dynamically

- **Test Buttons for All Providers** - Settings UI now has test buttons for:
  - Grocy connection (uses stored credentials via backend)
  - OpenFoodFacts, go-upc, UPCitemdb, Brave Search lookup providers
  - LLM connection with model count feedback

- **API Key Status Indicators** - Visual "Key Set" badges show when API keys are configured
  - Green badge appears next to provider name when key is saved
  - Placeholder text indicates "Leave blank to keep existing key"

- **LLM Integration Tests** - Test scripts for OpenAI/LLM functionality
  - `scripts/test_llm.py` - Health check, completion, product optimization
  - `scripts/test_brave_search.py` - Brave Search API integration
  - `scripts/test_models_api.py` - Models endpoint validation

- **Development Workflow Rule** - Cursor rule documenting local-to-remote deployment process

### Fixed

- LLM preset dropdown case sensitivity ("openai" vs "OpenAI")
- Grocy test button now uses stored credentials via backend endpoint
- Unicode symbols replaced with ASCII text for cross-platform compatibility
- LLM client now reads settings dynamically for hot-reload support

## [0.2.0-alpha] - 2026-02-02

### Added

- **Persistent Settings Storage** - Settings now stored in encrypted JSON file (`data/settings.json`)
  - Fernet encryption for sensitive values (API keys)
  - Settings service with load/save/update operations
  - REST API endpoints for settings management (`GET/PUT /api/settings/{section}`)

- **Lookup Provider API Keys UI** - Settings → Lookup tab now includes:
  - API key inputs for go-upc, UPCitemdb, and Brave Search
  - Enable/disable toggles for each provider
  - Provider descriptions and status badges

- **Hot-Reload for Settings** - Lookup provider settings take effect immediately without restart
  - Dynamic settings loading in all lookup providers
  - Automatic provider reload on settings save

- **Skip Cache Option** - Added `skip_cache` parameter to scan API for testing/debugging

- Test scripts for API validation (`scripts/test_api.py`, `scripts/test_settings.py`, `scripts/test_hot_reload.py`, `scripts/test_lookups.py`)

### Fixed

- Menu bar visibility - Navigation buttons now have proper contrast with `color=white` props and `bg-primary` header
- NiceGUI integration with FastAPI when running under uvicorn
- Circular import in UI layout components - moved to dedicated `app/ui/layout.py` module

### Changed

- Lookup providers refactored to read settings dynamically instead of caching at startup
- Settings UI updated to fetch/save via API instead of static config

## [0.1.0-alpha] - 2026-02-02

### Added

- **Core Scanning**
  - Barcode validation for EAN-13, EAN-8, UPC-A, UPC-E formats
  - Location barcode support (LOC-{AREA}-{NUMBER} format)
  - Camera scanning component for mobile devices
  - USB/Bluetooth scanner support (keyboard wedge)
  - Manual barcode entry

- **Product Lookup**
  - Multi-provider lookup system with configurable priority
  - OpenFoodFacts integration
  - go-upc integration
  - UPCItemDB integration
  - Brave Search fallback
  - Redis caching with 30-day TTL

- **LLM Integration**
  - Product name cleaning and optimization
  - Automatic category inference
  - Multi-source data merging
  - Support for OpenAI, Anthropic, Ollama via LiteLLM

- **Grocy Integration**
  - Product sync with Grocy inventory
  - Stock management (add, consume)
  - Location sync
  - Barcode association

- **User Interface**
  - NiceGUI-based responsive web UI
  - Mobile-optimized scanning page
  - Touch-friendly date picker with quick-select buttons
  - Product review popup (70% width)
  - Settings page with tabbed interface
  - Job queue viewer
  - Log viewer

- **Backend**
  - FastAPI REST API
  - PostgreSQL database with Alembic migrations
  - Background job queue system
  - Session-based authentication with bcrypt
  - Rate limiting middleware

- **Observability**
  - Structured JSON logging with structlog
  - OpenTelemetry tracing support
  - Prometheus metrics endpoint
  - Health check endpoints

- **Deployment**
  - Docker Compose configuration
  - Bare metal installation script
  - Environment variable configuration

### Security

- bcrypt password hashing (cost factor 12)
- Session management with idle and absolute timeouts
- Rate limiting (configurable, default 100 req/min)
- Input validation with Pydantic
- Secrets stored securely with SecretStr

## [0.0.1-alpha] - 2026-02-02

### Added

- Initial project scaffolding
- Basic project structure
