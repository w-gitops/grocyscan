"""Stock schemas for API v2."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class StockAddRequest(BaseModel):
    """Add stock request."""

    product_id: UUID
    location_id: UUID | None = None
    quantity: int = Field(..., gt=0)
    expiration_date: date | None = None


class StockConsumeRequest(BaseModel):
    """Consume stock request."""

    product_id: UUID
    location_id: UUID | None = None
    quantity: int = Field(..., gt=0)


class StockTransferRequest(BaseModel):
    """Transfer stock request."""

    product_id: UUID
    from_location_id: UUID
    to_location_id: UUID
    quantity: int = Field(..., gt=0)


class StockResponse(BaseModel):
    """Stock response."""

    id: UUID
    tenant_id: UUID
    product_id: UUID
    location_id: UUID | None
    quantity: int
    expiration_date: date | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
