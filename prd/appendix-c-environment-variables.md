# Appendix C: Environment Variable Reference

## Complete Environment Variable List

```bash
# ============================================
# APPLICATION CORE
# ============================================
GROCYSCAN_VERSION=1.0.0
GROCYSCAN_ENV=production              # development, staging, production
GROCYSCAN_DEBUG=false
GROCYSCAN_HOST=0.0.0.0
GROCYSCAN_PORT=3334
GROCYSCAN_SECRET_KEY=                 # Required: 32+ character secret

# ============================================
# API DOCUMENTATION
# ============================================
DOCS_ENABLED=true                     # Enable /docs and /redoc
OPENAPI_URL=/api/v1/openapi.json

# ============================================
# DATABASE
# ============================================
DATABASE_URL=postgresql://grocyscan:password@localhost:5432/grocyscan
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10
DATABASE_ECHO=false                   # Log SQL queries

# ============================================
# REDIS CACHE
# ============================================
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=
CACHE_TTL_DAYS=30

# ============================================
# GROCY INTEGRATION
# ============================================
GROCY_API_URL=http://192.168.1.100:9283    # Internal API URL
GROCY_API_KEY=                              # Required
GROCY_WEB_URL=https://grocy.example.com    # External URL for UI links
GROCY_TIMEOUT_SECONDS=30

# ============================================
# LLM CONFIGURATION
# ============================================
LLM_PROVIDER_PRESET=generic           # openai, anthropic, ollama, generic
LLM_API_URL=http://localhost:11434/v1
LLM_API_KEY=
LLM_MODEL=llama3.1:8b
LLM_TIMEOUT_SECONDS=60
LLM_MAX_RETRIES=3

# ============================================
# LOOKUP PROVIDERS
# ============================================
LOOKUP_STRATEGY=sequential            # sequential, parallel
LOOKUP_PROVIDER_ORDER=openfoodfacts,goupc,upcitemdb,brave,federation
LOOKUP_TIMEOUT_SECONDS=10

OPENFOODFACTS_ENABLED=true
OPENFOODFACTS_USER_AGENT=GrocyScan/1.0

GOUPC_ENABLED=true
GOUPC_API_KEY=

UPCITEMDB_ENABLED=true
UPCITEMDB_API_KEY=

BRAVE_ENABLED=true
BRAVE_API_KEY=
BRAVE_USE_AS_FALLBACK=true

FEDERATION_ENABLED=false
FEDERATION_URL=https://barcodebuddy.example.com

# ============================================
# SCANNING BEHAVIOR
# ============================================
AUTO_ADD_ENABLED=false
FUZZY_MATCH_THRESHOLD=0.9
DEFAULT_QUANTITY_UNIT=pieces
KIOSK_MODE_ENABLED=false

# ============================================
# AUTHENTICATION
# ============================================
AUTH_ENABLED=true
AUTH_USERNAME=admin
AUTH_PASSWORD_HASH=                   # bcrypt hash
SESSION_TIMEOUT_HOURS=24
SESSION_ABSOLUTE_TIMEOUT_DAYS=7

# External API Access
EXTERNAL_API_ENABLED=true
EXTERNAL_API_RATE_LIMIT=100          # requests per minute

# ============================================
# MCP SERVER
# ============================================
MCP_ENABLED=true
MCP_PORT=3335
MCP_TRANSPORT=streamable-http
MCP_REQUIRE_API_KEY=true

# ============================================
# OBSERVABILITY
# ============================================
LOG_LEVEL=INFO                        # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json                       # json, console
LOG_FILE=/var/log/grocyscan/app.log

OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_EXPORTER_OTLP_INSECURE=true
OTEL_SERVICE_NAME=grocyscan

METRICS_ENABLED=true
METRICS_PORT=3334

# ============================================
# BROTHER QL PRINTING (Post-MVP)
# ============================================
BROTHER_QL_ENABLED=false
BROTHER_QL_WEB_URL=http://localhost:8013
```

## Provider-Specific Configuration

### OpenAI Preset
```bash
LLM_PROVIDER_PRESET=openai
LLM_API_URL=https://api.openai.com/v1
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
```

### Anthropic Preset
```bash
LLM_PROVIDER_PRESET=anthropic
LLM_API_URL=https://api.anthropic.com/v1
LLM_API_KEY=sk-ant-...
LLM_MODEL=claude-3-haiku-20240307
```

### Ollama Preset
```bash
LLM_PROVIDER_PRESET=ollama
LLM_API_URL=http://localhost:11434/v1
LLM_API_KEY=
LLM_MODEL=llama3.1:8b
```

---

## Navigation

- **Previous:** [Appendix B - MCP Server](appendix-b-mcp-server.md)
- **Next:** [Appendix D - Troubleshooting](appendix-d-troubleshooting.md)
- **Back to:** [README](README.md)
