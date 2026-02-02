"""SQLAlchemy ORM models for GrocyScan."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.database import Base

if TYPE_CHECKING:
    pass


class User(Base):
    """User model - MVP has single user, pre-designed for multi-user."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    products: Mapped[list["Product"]] = relationship("Product", back_populates="user")
    barcodes: Mapped[list["Barcode"]] = relationship("Barcode", back_populates="user")
    stock_entries: Mapped[list["StockEntry"]] = relationship(
        "StockEntry", back_populates="user"
    )
    locations: Mapped[list["Location"]] = relationship("Location", back_populates="user")
    jobs: Mapped[list["Job"]] = relationship("Job", back_populates="user")
    scan_history: Mapped[list["ScanHistory"]] = relationship(
        "ScanHistory", back_populates="user"
    )
    settings: Mapped[list["Setting"]] = relationship("Setting", back_populates="user")


class Product(Base):
    """Local product cache with Grocy sync."""

    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    grocy_product_id: Mapped[int | None] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    name_normalized: Mapped[str | None] = mapped_column(String(500), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(255), index=True)
    quantity_unit: Mapped[str | None] = mapped_column(String(50))
    image_path: Mapped[str | None] = mapped_column(String(500))
    image_uploaded_to_grocy: Mapped[bool] = mapped_column(Boolean, default=False)
    nutrition_json: Mapped[dict | None] = mapped_column(JSON)
    llm_optimized: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_lookup_data: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="products")
    barcodes: Mapped[list["Barcode"]] = relationship("Barcode", back_populates="product")
    stock_entries: Mapped[list["StockEntry"]] = relationship(
        "StockEntry", back_populates="product"
    )
    scan_history: Mapped[list["ScanHistory"]] = relationship(
        "ScanHistory", back_populates="product"
    )

    __table_args__ = (
        Index("ix_products_user_name_normalized", "user_id", "name_normalized"),
        Index("ix_products_user_grocy_id", "user_id", "grocy_product_id"),
    )


class Barcode(Base):
    """Multiple barcodes can map to one product."""

    __tablename__ = "barcodes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=True, index=True
    )
    barcode: Mapped[str] = mapped_column(String(100), nullable=False)
    barcode_type: Mapped[str | None] = mapped_column(String(20))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="barcodes")
    product: Mapped["Product | None"] = relationship("Product", back_populates="barcodes")

    __table_args__ = (Index("ix_barcodes_user_barcode", "user_id", "barcode", unique=True),)


class Location(Base):
    """Storage locations synced with Grocy."""

    __tablename__ = "locations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    grocy_location_id: Mapped[int | None] = mapped_column(Integer, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_freezer: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="locations")
    stock_entries: Mapped[list["StockEntry"]] = relationship(
        "StockEntry", back_populates="location"
    )
    scan_history: Mapped[list["ScanHistory"]] = relationship(
        "ScanHistory", back_populates="location"
    )

    __table_args__ = (Index("ix_locations_user_code", "user_id", "code", unique=True),)


class StockEntry(Base):
    """Individual stock entries for expiration tracking."""

    __tablename__ = "stock_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True, index=True
    )
    grocy_stock_id: Mapped[int | None] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    best_before: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    purchased_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    price: Mapped[str | None] = mapped_column(String(20))
    note: Mapped[str | None] = mapped_column(Text)
    synced_to_grocy: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="stock_entries")
    product: Mapped["Product"] = relationship("Product", back_populates="stock_entries")
    location: Mapped["Location | None"] = relationship(
        "Location", back_populates="stock_entries"
    )

    __table_args__ = (Index("ix_stock_entries_user_best_before", "user_id", "best_before"),)


class LookupCache(Base):
    """Cache for barcode lookup results."""

    __tablename__ = "lookup_cache"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    barcode: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    response_json: Mapped[dict | None] = mapped_column(JSON)
    optimized_json: Mapped[dict | None] = mapped_column(JSON)
    image_url: Mapped[str | None] = mapped_column(String(1000))
    image_local_path: Mapped[str | None] = mapped_column(String(500))
    lookup_success: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    __table_args__ = (
        Index("ix_lookup_cache_barcode_provider", "barcode", "provider", unique=True),
    )


class Job(Base):
    """Background job queue for async operations."""

    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    priority: Mapped[int] = mapped_column(Integer, default=0, index=True)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    result_json: Mapped[dict | None] = mapped_column(JSON)
    error_message: Mapped[str | None] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="jobs")

    __table_args__ = (
        Index("ix_jobs_status_priority_scheduled", "status", "priority", "scheduled_at"),
    )


class ScanHistory(Base):
    """Audit log of all scans."""

    __tablename__ = "scan_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    barcode: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=True
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    input_method: Mapped[str | None] = mapped_column(String(20))
    best_before: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lookup_provider: Mapped[str | None] = mapped_column(String(50))
    lookup_duration_ms: Mapped[int | None] = mapped_column(Integer)
    llm_optimized: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    request_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="scan_history")
    product: Mapped["Product | None"] = relationship("Product", back_populates="scan_history")
    location: Mapped["Location | None"] = relationship("Location", back_populates="scan_history")

    __table_args__ = (Index("ix_scan_history_user_created", "user_id", "created_at"),)


class Setting(Base):
    """User-specific settings stored as key-value pairs."""

    __tablename__ = "settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="settings")

    __table_args__ = (Index("ix_settings_user_key", "user_id", "key", unique=True),)
