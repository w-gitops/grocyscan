# Changelog

All notable changes to GrocyScan will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-02

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

## [0.1.0] - 2026-02-02

### Added

- Initial project scaffolding
- Basic project structure
