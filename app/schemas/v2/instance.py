"""Product instance (LPN) schemas (Phase 4)."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProductInstanceCreate(BaseModel):
    """Create product instance."""

    product_id: UUID = Field(...)
    location_id: UUID | None = None
    lpn: str | None = Field(None, max_length=100)
    remaining_quantity: int = Field(1, ge=1)
    expiration_date: date | None = None


class ProductInstanceConsume(BaseModel):
    """Consume from instance."""

    quantity: int = Field(1, ge=1)


class ProductInstanceResponse(BaseModel):
    """Product instance response."""

    id: UUID
    tenant_id: UUID
    product_id: UUID
    location_id: UUID | None
    lpn: str | None
    remaining_quantity: int
    expiration_date: date | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
