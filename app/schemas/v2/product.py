"""Product schemas for API v2."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    """Create product request."""

    name: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    category: str | None = None
    quantity_unit: str | None = None
    min_stock_quantity: int = Field(default=0, ge=0)
    attributes: dict | None = None
    barcode: str | None = Field(None, max_length=100)


class ProductUpdate(BaseModel):
    """Update product request (partial)."""

    name: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    category: str | None = None
    quantity_unit: str | None = None
    min_stock_quantity: int | None = Field(None, ge=0)
    attributes: dict | None = None


class ProductResponse(BaseModel):
    """Product response."""

    id: UUID
    tenant_id: UUID
    name: str
    name_normalized: str | None
    description: str | None
    category: str | None
    quantity_unit: str | None
    min_stock_quantity: int
    attributes: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
