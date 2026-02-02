# 6. API Specification

## 6.1 API Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/scan` | POST | Process a barcode scan |
| `/api/scan/{scan_id}/confirm` | POST | Confirm and add scanned product |
| `/api/scan/{scan_id}/select` | POST | Select from multiple candidates |
| `/api/products` | GET | List/search products |
| `/api/products` | POST | Create new product |
| `/api/products/{id}` | GET | Get product details |
| `/api/products/{id}` | PUT | Update product |
| `/api/products/{id}` | DELETE | Delete product |
| `/api/products/search` | POST | Search products by name |
| `/api/locations` | GET | List locations |
| `/api/locations` | POST | Create location |
| `/api/locations/{code}` | GET | Get location by code |
| `/api/locations/{code}/print` | POST | Print location label |
| `/api/jobs` | GET | List job queue |
| `/api/jobs/{id}` | GET | Get job details |
| `/api/jobs/{id}/retry` | POST | Retry failed job |
| `/api/jobs/{id}/cancel` | POST | Cancel pending job |
| `/api/settings` | GET | Get current settings |
| `/api/settings` | PUT | Update settings |
| `/api/logs` | GET | Get application logs |
| `/api/auth/login` | POST | Authenticate user |
| `/api/auth/logout` | POST | Logout user |
| `/api/health` | GET | Health check |
| `/metrics` | GET | Prometheus metrics |

## 6.2 Pydantic Schemas

### Scan Schemas

```python
# app/schemas/scan.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


class InputMethod(str, Enum):
    CAMERA = "camera"
    SCANNER = "scanner"
    MANUAL = "manual"


class ScanRequest(BaseModel):
    """Request to scan and process a barcode."""
    barcode: str = Field(..., min_length=1, max_length=100, description="Barcode value")
    input_method: InputMethod = InputMethod.SCANNER
    location_code: Optional[str] = Field(None, description="Current location code (LOC-XXX)")
    best_before: Optional[datetime] = Field(None, description="Expiration date")
    auto_add: Optional[bool] = Field(None, description="Override auto-add setting")


class ScanResponse(BaseModel):
    """Response from scan operation."""
    scan_id: UUID
    status: str  # found, not_found, pending_review, added, error
    barcode: str
    product: Optional["ProductDetail"] = None
    candidates: Optional[list["ProductCandidate"]] = None
    requires_review: bool = False
    job_id: Optional[UUID] = None  # If LLM optimization queued
    message: str


class ProductCandidate(BaseModel):
    """Potential product match for user selection."""
    product_id: Optional[UUID] = None
    grocy_product_id: Optional[int] = None
    name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    source: str  # local, grocy, lookup
    image_url: Optional[str] = None


class ProductDetail(BaseModel):
    """Full product details."""
    id: Optional[UUID] = None
    grocy_product_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    quantity_unit: Optional[str] = None
    image_url: Optional[str] = None
    nutrition: Optional[dict] = None
    barcodes: list[str] = []
    llm_optimized: bool = False
    lookup_provider: Optional[str] = None
```

### Product Schemas

```python
# app/schemas/product.py
class ProductCreate(BaseModel):
    """Create a new product."""
    name: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    category: Optional[str] = None
    quantity_unit: Optional[str] = "pieces"
    barcodes: list[str] = []
    add_to_grocy: bool = True
    add_stock: bool = False
    location_code: Optional[str] = None
    best_before: Optional[datetime] = None


class ProductUpdate(BaseModel):
    """Update an existing product."""
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    category: Optional[str] = None
    quantity_unit: Optional[str] = None


class ProductSearch(BaseModel):
    """Search parameters for products."""
    query: str = Field(..., min_length=1)
    include_grocy: bool = True
    limit: int = Field(20, ge=1, le=100)
```

### Location Schemas

```python
# app/schemas/location.py
class LocationCreate(BaseModel):
    """Create a new location."""
    code: str = Field(..., pattern=r"^LOC-[A-Z0-9]+-[0-9]+$")
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_freezer: bool = False
    sync_to_grocy: bool = True


class LocationResponse(BaseModel):
    """Location response."""
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    is_freezer: bool
    grocy_location_id: Optional[int] = None
```

### Job Schemas

```python
# app/schemas/job.py
class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    LLM_OPTIMIZE = "llm_optimize"
    GROCY_SYNC = "grocy_sync"
    IMAGE_DOWNLOAD = "image_download"
    OFFLINE_SYNC = "offline_sync"


class JobResponse(BaseModel):
    """Job queue item response."""
    id: UUID
    job_type: JobType
    status: JobStatus
    payload: dict
    result: Optional[dict] = None
    error_message: Optional[str] = None
    attempts: int
    max_attempts: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class JobRetry(BaseModel):
    """Retry a failed job."""
    job_id: UUID
    reset_attempts: bool = False
```

### Settings Schemas

```python
# app/schemas/settings.py
class LLMProviderPreset(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    GENERIC = "generic"


class LookupStrategy(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"


class SettingsUpdate(BaseModel):
    """Update application settings."""
    # Grocy connection
    grocy_api_url: Optional[str] = None
    grocy_api_key: Optional[str] = None
    grocy_web_url: Optional[str] = None

    # LLM configuration
    llm_provider_preset: Optional[LLMProviderPreset] = None
    llm_api_url: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_model: Optional[str] = None

    # Lookup configuration
    lookup_strategy: Optional[LookupStrategy] = None
    lookup_provider_order: Optional[list[str]] = None
    lookup_cache_ttl_days: Optional[int] = None

    # Provider API keys
    goupc_api_key: Optional[str] = None
    upcitemdb_api_key: Optional[str] = None
    brave_api_key: Optional[str] = None

    # Scanning behavior
    auto_add_enabled: Optional[bool] = None
    fuzzy_match_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    default_quantity_unit: Optional[str] = None

    # UI preferences
    dark_mode: Optional[bool] = None
    kiosk_mode: Optional[bool] = None


class SettingsResponse(BaseModel):
    """Current settings (sensitive fields redacted)."""
    grocy_api_url: Optional[str] = None
    grocy_api_key_set: bool = False
    grocy_web_url: Optional[str] = None

    llm_provider_preset: LLMProviderPreset = LLMProviderPreset.GENERIC
    llm_api_url: Optional[str] = None
    llm_api_key_set: bool = False
    llm_model: Optional[str] = None

    lookup_strategy: LookupStrategy = LookupStrategy.SEQUENTIAL
    lookup_provider_order: list[str] = []
    lookup_cache_ttl_days: int = 30

    goupc_api_key_set: bool = False
    upcitemdb_api_key_set: bool = False
    brave_api_key_set: bool = False

    auto_add_enabled: bool = False
    fuzzy_match_threshold: float = 0.9
    default_quantity_unit: str = "pieces"

    dark_mode: bool = False
    kiosk_mode: bool = False
```

## 6.3 API Error Responses

```python
# app/core/exceptions.py
from fastapi import HTTPException
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    message: str
    details: dict | None = None
    request_id: str | None = None


class GrocyScanException(Exception):
    """Base exception for GrocyScan."""
    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details


class BarcodeNotFoundError(GrocyScanException):
    """Barcode not found in any lookup provider."""
    pass


class GrocyConnectionError(GrocyScanException):
    """Failed to connect to Grocy API."""
    pass


class LLMError(GrocyScanException):
    """LLM provider error."""
    pass


class LookupProviderError(GrocyScanException):
    """External lookup provider error."""
    pass
```

---

## Navigation

- **Previous:** [Data Models](05-data-models.md)
- **Next:** [UI Specification](07-ui-specification.md)
- **Back to:** [README](README.md)
