# Changelog

All notable changes to GrocyScan will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
