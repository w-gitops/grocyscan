# 5. Data Models

## 5.1 Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA MODEL                                      │
│                                                                              │
│  ┌─────────────┐       ┌─────────────────┐       ┌─────────────────────┐    │
│  │   users     │       │    products     │       │     barcodes        │    │
│  │─────────────│       │─────────────────│       │─────────────────────│    │
│  │ id (PK)     │──┐    │ id (PK)         │◄──────│ id (PK)             │    │
│  │ email       │  │    │ user_id (FK)    │──┐    │ barcode             │    │
│  │ password    │  │    │ grocy_id        │  │    │ product_id (FK)     │    │
│  │ is_active   │  │    │ name            │  │    │ user_id (FK)        │────┤
│  │ created_at  │  │    │ category        │  │    │ created_at          │    │
│  │ updated_at  │  │    │ image_path      │  │    └─────────────────────┘    │
│  └─────────────┘  │    │ nutrition_json  │  │                               │
│        │          │    │ created_at      │  │    ┌─────────────────────┐    │
│        │          │    │ updated_at      │  │    │   stock_entries     │    │
│        │          │    └─────────────────┘  │    │─────────────────────│    │
│        │          │             │           │    │ id (PK)             │    │
│        │          │             │           │    │ product_id (FK)     │────┤
│        │          │             ▼           │    │ location_id (FK)    │────┤
│        │          │    ┌─────────────────┐  │    │ user_id (FK)        │────┤
│        │          │    │  lookup_cache   │  │    │ quantity            │    │
│        │          │    │─────────────────│  │    │ best_before         │    │
│        │          │    │ id (PK)         │  │    │ grocy_stock_id      │    │
│        │          │    │ barcode         │  │    │ created_at          │    │
│        │          │    │ provider        │  │    └─────────────────────┘    │
│        │          │    │ response_json   │  │                               │
│        │          │    │ optimized_json  │  │    ┌─────────────────────┐    │
│        │          │    │ image_url       │  │    │     locations       │    │
│        │          │    │ created_at      │  │    │─────────────────────│    │
│        │          │    │ expires_at      │  │    │ id (PK)             │    │
│        │          │    └─────────────────┘  │    │ user_id (FK)        │────┤
│        │          │                         │    │ code                │    │
│        │          │                         │    │ name                │    │
│        │          └─────────────────────────│────│ grocy_location_id   │    │
│        │                                    │    │ created_at          │    │
│        │                                    │    └─────────────────────┘    │
│        │          ┌─────────────────────────┘                               │
│        │          │                                                          │
│        │          │    ┌─────────────────┐       ┌─────────────────────┐    │
│        │          │    │   job_queue     │       │   scan_history      │    │
│        │          │    │─────────────────│       │─────────────────────│    │
│        │          │    │ id (PK)         │       │ id (PK)             │    │
│        └──────────│────│ user_id (FK)    │       │ user_id (FK)        │────┤
│                   │    │ job_type        │       │ barcode             │    │
│                   │    │ payload_json    │       │ product_id (FK)     │────┘
│                   │    │ status          │       │ location_id (FK)    │
│                   │    │ attempts        │       │ action              │
│                   │    │ error_message   │       │ created_at          │
│                   │    │ created_at      │       └─────────────────────┘
│                   │    │ updated_at      │
│                   │    └─────────────────┘       ┌─────────────────────┐
│                   │                              │     settings        │
│                   │                              │─────────────────────│
│                   │                              │ id (PK)             │
│                   └──────────────────────────────│ user_id (FK)        │
│                                                  │ key                 │
│                                                  │ value_json          │
│                                                  │ updated_at          │
│                                                  └─────────────────────┘
└─────────────────────────────────────────────────────────────────────────────┘
```

## 5.2 SQLAlchemy Models

```python
# app/db/models.py
from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, Text, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class User(Base):
    """User model - MVP has single user, pre-designed for multi-user."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    products = relationship("Product", back_populates="user")
    barcodes = relationship("Barcode", back_populates="user")
    stock_entries = relationship("StockEntry", back_populates="user")
    locations = relationship("Location", back_populates="user")
    jobs = relationship("Job", back_populates="user")
    scan_history = relationship("ScanHistory", back_populates="user")
    settings = relationship("Setting", back_populates="user")


class Product(Base):
    """Local product cache with Grocy sync."""
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    grocy_product_id = Column(Integer, index=True)  # Grocy's product ID
    name = Column(String(500), nullable=False)
    name_normalized = Column(String(500), index=True)  # Lowercase for fuzzy matching
    description = Column(Text)
    category = Column(String(255), index=True)
    quantity_unit = Column(String(50))  # e.g., "pieces", "grams", "ml"
    image_path = Column(String(500))  # Local storage path
    image_uploaded_to_grocy = Column(Boolean, default=False)
    nutrition_json = Column(JSON)  # Structured nutrition data
    llm_optimized = Column(Boolean, default=False)
    raw_lookup_data = Column(JSON)  # Original lookup response
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="products")
    barcodes = relationship("Barcode", back_populates="product")
    stock_entries = relationship("StockEntry", back_populates="product")
    scan_history = relationship("ScanHistory", back_populates="product")

    # Indexes for fuzzy matching
    __table_args__ = (
        Index("ix_products_user_name_normalized", "user_id", "name_normalized"),
        Index("ix_products_user_grocy_id", "user_id", "grocy_product_id"),
    )


class Barcode(Base):
    """Multiple barcodes can map to one product."""
    __tablename__ = "barcodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True, index=True)
    barcode = Column(String(100), nullable=False)
    barcode_type = Column(String(20))  # UPC-A, EAN-13, etc.
    is_primary = Column(Boolean, default=False)  # Primary barcode for product
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="barcodes")
    product = relationship("Product", back_populates="barcodes")

    __table_args__ = (
        Index("ix_barcodes_user_barcode", "user_id", "barcode", unique=True),
    )


class Location(Base):
    """Storage locations synced with Grocy."""
    __tablename__ = "locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    grocy_location_id = Column(Integer, index=True)
    code = Column(String(50), nullable=False)  # e.g., LOC-PANTRY-01
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_freezer = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="locations")
    stock_entries = relationship("StockEntry", back_populates="location")
    scan_history = relationship("ScanHistory", back_populates="location")

    __table_args__ = (
        Index("ix_locations_user_code", "user_id", "code", unique=True),
    )


class StockEntry(Base):
    """Individual stock entries for expiration tracking."""
    __tablename__ = "stock_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True, index=True)
    grocy_stock_id = Column(Integer)  # Grocy's stock entry ID
    quantity = Column(Integer, nullable=False, default=1)
    best_before = Column(DateTime(timezone=True), index=True)
    purchased_date = Column(DateTime(timezone=True), server_default=func.now())
    price = Column(String(20))  # Store as string for currency flexibility
    note = Column(Text)
    synced_to_grocy = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="stock_entries")
    product = relationship("Product", back_populates="stock_entries")
    location = relationship("Location", back_populates="stock_entries")

    __table_args__ = (
        Index("ix_stock_entries_user_best_before", "user_id", "best_before"),
    )


class LookupCache(Base):
    """Cache for barcode lookup results."""
    __tablename__ = "lookup_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    barcode = Column(String(100), nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # openfoodfacts, goupc, etc.
    response_json = Column(JSON)  # Raw API response
    optimized_json = Column(JSON)  # LLM-optimized data
    image_url = Column(String(1000))
    image_local_path = Column(String(500))
    lookup_success = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    __table_args__ = (
        Index("ix_lookup_cache_barcode_provider", "barcode", "provider", unique=True),
    )


class Job(Base):
    """Background job queue for async operations."""
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    job_type = Column(String(50), nullable=False)  # llm_optimize, grocy_sync, image_download
    status = Column(String(20), nullable=False, default="pending", index=True)
    priority = Column(Integer, default=0, index=True)  # Higher = more urgent
    payload_json = Column(JSON, nullable=False)  # Job-specific data
    result_json = Column(JSON)  # Job result
    error_message = Column(Text)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    scheduled_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="jobs")

    __table_args__ = (
        Index("ix_jobs_status_priority_scheduled", "status", "priority", "scheduled_at"),
    )


class ScanHistory(Base):
    """Audit log of all scans."""
    __tablename__ = "scan_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    barcode = Column(String(100), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True)
    action = Column(String(50), nullable=False)  # added, skipped, failed, created
    input_method = Column(String(20))  # camera, scanner, manual
    best_before = Column(DateTime(timezone=True))
    lookup_provider = Column(String(50))  # Which provider found the product
    lookup_duration_ms = Column(Integer)
    llm_optimized = Column(Boolean, default=False)
    error_message = Column(Text)
    request_id = Column(UUID(as_uuid=True))  # For tracing
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="scan_history")
    product = relationship("Product", back_populates="scan_history")
    location = relationship("Location", back_populates="scan_history")

    __table_args__ = (
        Index("ix_scan_history_user_created", "user_id", "created_at"),
    )


class Setting(Base):
    """User-specific settings stored as key-value pairs."""
    __tablename__ = "settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    key = Column(String(100), nullable=False)
    value_json = Column(JSON, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="settings")

    __table_args__ = (
        Index("ix_settings_user_key", "user_id", "key", unique=True),
    )
```

## 5.3 Key Pydantic Schemas

See [API Specification](06-api-specification.md) for complete Pydantic schemas.

---

## Navigation

- **Previous:** [Technical Architecture](04-technical-architecture.md)
- **Next:** [API Specification](06-api-specification.md)
- **Back to:** [README](README.md)
