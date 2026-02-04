"""SQLAlchemy models for homebot schema (Phase 2+)."""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.database import Base

if TYPE_CHECKING:
    pass


class HomebotTenant(Base):
    """Tenant in homebot schema (minimal ORM so FK from devices/products/etc. resolve)."""

    __tablename__ = "tenants"
    __table_args__ = {"schema": "homebot"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    settings: Mapped[dict | None] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class HomebotUser(Base):
    """User in homebot schema (tenant-scoped login identity)."""

    __tablename__ = "users"
    __table_args__ = {"schema": "homebot"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("homebot.tenants.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class HomebotPerson(Base):
    """Household member profile in homebot schema."""

    __tablename__ = "people"
    __table_args__ = {"schema": "homebot"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("homebot.tenants.id"), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("homebot.users.id"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(50))
    avatar_url: Mapped[str | None] = mapped_column(Text)
    color: Mapped[str | None] = mapped_column(String(7))
    dietary_restrictions: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    allergies: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class HomebotProduct(Base):
    """Product in homebot schema."""

    __tablename__ = "products"
    __table_args__ = {"schema": "homebot"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("homebot.tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    name_normalized: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(255))
    quantity_unit: Mapped[str | None] = mapped_column(String(50))
    min_stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    image_path: Mapped[str | None] = mapped_column(String(500))
    attributes: Mapped[dict | None] = mapped_column(JSON, default=dict)
    enable_lpn_tracking: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    barcodes: Mapped[list["HomebotBarcode"]] = relationship("HomebotBarcode", back_populates="product")


class HomebotBarcode(Base):
    """Barcode in homebot schema."""

    __tablename__ = "barcodes"
    __table_args__ = {"schema": "homebot"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("homebot.tenants.id"), nullable=False)
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("homebot.products.id"))
    barcode: Mapped[str] = mapped_column(String(100), nullable=False)
    barcode_type: Mapped[str | None] = mapped_column(String(20))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product: Mapped["HomebotProduct | None"] = relationship("HomebotProduct", back_populates="barcodes")


class HomebotLocation(Base):
    """Location in homebot schema."""

    __tablename__ = "locations"
    __table_args__ = {"schema": "homebot"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("homebot.tenants.id"), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("homebot.locations.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location_type: Mapped[str] = mapped_column(String(50), nullable=False)
    path: Mapped[str | None] = mapped_column(String(1000))
    description: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_freezer: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    parent: Mapped["HomebotLocation | None"] = relationship("HomebotLocation", remote_side="HomebotLocation.id")


class HomebotLocationClosure(Base):
    """Location closure table for hierarchy queries."""

    __tablename__ = "location_closure"
    __table_args__ = {"schema": "homebot"}

    ancestor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("homebot.locations.id"),
        primary_key=True,
    )
    descendant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("homebot.locations.id"),
        primary_key=True,
    )
    depth: Mapped[int] = mapped_column(Integer, nullable=False)


class HomebotStock(Base):
    """Stock in homebot schema."""

    __tablename__ = "stock"
    __table_args__ = {"schema": "homebot"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("homebot.tenants.id"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("homebot.products.id"), nullable=False)
    location_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("homebot.locations.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    expiration_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class HomebotStockTransaction(Base):
    """Stock transaction audit in homebot schema."""

    __tablename__ = "stock_transactions"
    __table_args__ = {"schema": "homebot"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("homebot.tenants.id"), nullable=False)
    stock_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("homebot.stock.id"))
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    from_location_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("homebot.locations.id"))
    to_location_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("homebot.locations.id"))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class HomebotDevice(Base):
    """Device registration and preferences in homebot schema (Phase 3)."""

    __tablename__ = "devices"
    __table_args__ = {"schema": "homebot"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("homebot.tenants.id"), nullable=False)
    # user_id references homebot.users.id in DB; no ORM FK so we don't need HomebotUser mapped
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(255), nullable=False)
    device_type: Mapped[str] = mapped_column(String(50), nullable=False)
    default_location_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("homebot.locations.id"))
    default_action: Mapped[str] = mapped_column(String(50), nullable=False, default="add_stock")
    scanner_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="camera")
    preferences: Mapped[dict | None] = mapped_column(JSON, default=dict)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
