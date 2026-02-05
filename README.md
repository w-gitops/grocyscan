# GrocyScan

Barcode scanning app for Grocy inventory management with multi-source product lookups, LLM-powered data optimization, and full observability.

## Features

- **Multi-Source Barcode Lookup**: OpenFoodFacts, go-upc, UPCItemDB, Brave Search
- **LLM-Powered Optimization**: Automatic name cleaning and category inference via LiteLLM
- **Grocy Integration**: Seamless product sync and stock management
- **Mobile-Friendly UI**: Vue 3 + Quasar PWA with touch-friendly controls
- **Offline Support**: Queue operations for sync when connectivity restored
- **Full Observability**: Structured logging, OpenTelemetry tracing, Prometheus metrics

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 17
- Redis (for caching)
- Docker and Docker Compose (optional)

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/grocyscan.git
   cd grocyscan
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .venv\Scripts\activate     # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. Copy and configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Start development services (PostgreSQL, Redis):
   ```bash
   docker compose -f docker/docker-compose.dev.yml up -d
   ```

6. Run database migrations:
   ```bash
   alembic upgrade head
   ```

7. Start the application:
   ```bash
   python -m app.main
   ```

8. Build and start the frontend:
   ```bash
   cd frontend
   npm install
   npm run build
   ```

9. Open http://localhost:3335 in your browser (API at :3334).

### Docker Deployment

```bash
# Build and run all services
docker compose -f docker/docker-compose.yml up -d

# View logs
docker compose -f docker/docker-compose.yml logs -f app
```

## Configuration

All configuration is via environment variables. See `.env.example` for all options.

### Key Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `GROCYSCAN_PORT` | Application port | 3334 |
| `DATABASE_URL` | PostgreSQL connection URL | Required |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `GROCY_API_URL` | Grocy API URL | Required |
| `GROCY_API_KEY` | Grocy API key | Required |
| `LLM_API_URL` | LLM API endpoint | `http://localhost:11434/v1` |
| `LLM_MODEL` | LLM model name | `llama3.1:8b` |

### Grocy custom fields (Brand)

To store **Brand** in Grocy when adding products via scan, add a userfield named `Brand` for the `products` entity in Grocy (Settings → Userfields). See [docs/GROCY-USERFIELDS.md](docs/GROCY-USERFIELDS.md) for step-by-step setup and how LLM enhancement uses it.

### Lookup Providers

Configure provider order and API keys:

```bash
LOOKUP_STRATEGY=sequential  # or parallel
LOOKUP_PROVIDER_ORDER=openfoodfacts,goupc,upcitemdb,brave

OPENFOODFACTS_ENABLED=true
GOUPC_ENABLED=true
GOUPC_API_KEY=your-api-key
```

## API Documentation

When `DOCS_ENABLED=true`, API documentation is available at:

- Swagger UI: http://localhost:3334/docs
- ReDoc: http://localhost:3334/redoc
- OpenAPI JSON: http://localhost:3334/api/v1/openapi.json

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/scan` | POST | Process barcode scan |
| `/api/scan/{id}/confirm` | POST | Confirm and add product |
| `/api/products` | GET | List products |
| `/api/locations` | GET | List locations |
| `/api/jobs` | GET | List background jobs |
| `/metrics` | GET | Prometheus metrics |

## Project Structure

```
grocyscan/
├── app/
│   ├── api/           # REST API endpoints
│   ├── core/          # Cross-cutting concerns
│   ├── db/            # Database models and CRUD
│   ├── schemas/       # Pydantic models
│   ├── services/      # Business logic
│   │   ├── lookup/    # Barcode lookup providers
│   │   ├── llm/       # LLM integration
│   │   ├── grocy/     # Grocy API client
│   │   └── queue/     # Background job queue
├── frontend/          # Vue 3 + Quasar frontend
├── migrations/        # Alembic migrations
├── tests/             # Test suite
├── docker/            # Docker configuration
└── prd/               # Product requirements
```

## Testing

```bash
# Tests require PostgreSQL (DATABASE_URL).
# Start a local test DB:
docker compose -f docker/docker-compose.test.yml up -d

# Run all tests (explicit URL)
DATABASE_URL=postgresql+asyncpg://grocyscan:grocyscan@localhost:5432/grocyscan_test \
  python -m pytest tests/ -v --tb=short

# Makefile helpers
make test-db-up
make test
make test-db-down

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_barcode.py
```

## Observability

### Logging

Structured JSON logs with OpenTelemetry trace context:

```json
{
  "timestamp": "2026-02-02T00:15:32.123456Z",
  "level": "INFO",
  "message": "Barcode scanned",
  "trace_id": "abc123...",
  "barcode": "4006381333931"
}
```

### Metrics

Prometheus metrics available at `/metrics`:

- `grocyscan_scans_total` - Total scans by status
- `grocyscan_lookup_duration_seconds` - Lookup duration histogram
- `grocyscan_grocy_operations_total` - Grocy API operations
- `grocyscan_job_queue_size` - Current job queue size

### Tracing

Configure OpenTelemetry exporter:

```bash
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

## Development

### Code Quality

```bash
# Format code
black app/ tests/

# Lint
ruff check app/ tests/

# Type check
mypy app/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## Support

- [Documentation](prd/README.md)
- [Troubleshooting](prd/appendix-d-troubleshooting.md)
- [GitHub Issues](https://github.com/yourusername/grocyscan/issues)
