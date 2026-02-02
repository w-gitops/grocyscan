# Appendix A: API Documentation & External Access

## A.1 Interactive API Documentation

FastAPI automatically generates interactive documentation based on the OpenAPI standard.

### Documentation Endpoints

| Endpoint | UI | Description |
|----------|-----|-------------|
| `/docs` | Swagger UI | Interactive exploration and testing |
| `/redoc` | ReDoc | Alternative API documentation |
| `/api/v1/openapi.json` | JSON Schema | Raw OpenAPI specification |

## A.2 FastAPI Configuration

```python
# app/main.py
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="GrocyScan API",
    description="""
    GrocyScan - Intelligent Barcode Inventory Manager
    
    ## Features
    * Barcode scanning and lookup
    * Multi-provider product lookup
    * LLM-powered product data optimization
    * Grocy integration for inventory management
    """,
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="GrocyScan API",
        version="1.0.0",
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

## A.3 External Application Access

External programs can call GrocyScan for lookups via the external API.

### External API Endpoints

```python
# app/api/external.py
from fastapi import APIRouter, Depends, Query
from app.api.auth import verify_api_key

router = APIRouter(prefix="/api/v1/external", tags=["external"])


@router.get("/lookup/{barcode}")
async def external_barcode_lookup(
    barcode: str,
    include_image: bool = Query(True),
    api_key: str = Depends(verify_api_key)
):
    """
    Look up product information by barcode.
    
    **Rate Limit:** 100 requests/minute per API key
    """
    pass


@router.post("/lookup/batch")
async def external_batch_lookup(
    barcodes: list[str],
    api_key: str = Depends(verify_api_key)
):
    """Look up multiple barcodes (max 50 per request)."""
    pass
```

## A.4 Usage Examples

### cURL

```bash
# Lookup a barcode
curl -X GET "http://localhost:3334/api/v1/external/lookup/012345678901" \
  -H "X-API-Key: your-api-key-here"

# Batch lookup
curl -X POST "http://localhost:3334/api/v1/external/lookup/batch" \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"barcodes": ["012345678901", "987654321098"]}'
```

### Python

```python
import httpx

client = httpx.Client(
    base_url="http://localhost:3334",
    headers={"X-API-Key": "your-api-key-here"}
)

response = client.get("/api/v1/external/lookup/012345678901")
product = response.json()
print(f"Product: {product['name']}")
```

---

## Navigation

- **Previous:** [Delivery Plan](14-delivery-plan.md)
- **Next:** [Appendix B - MCP Server](appendix-b-mcp-server.md)
- **Back to:** [README](README.md)
