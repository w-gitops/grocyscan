"""Stock schemas for API v2."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class StockAddRequest(BaseModel):
    """Add stock request."""

    product_id: UUID
    location_id: UUID | None = None
    quantity: Decimal = Field(..., gt=0)
    expiration_date: date | None = None
    price: Decimal | None = None
    purchased_date: date | None = None
    note: str | None = None


class StockConsumeRequest(BaseModel):
    """Consume stock request."""

    product_id: UUID
    location_id: UUID | None = None
    quantity: Decimal = Field(..., gt=0)
    spoiled: bool = False


class StockTransferRequest(BaseModel):
    """Transfer stock request."""

    product_id: UUID
    from_location_id: UUID
    to_location_id: UUID
    quantity: Decimal = Field(..., gt=0)


class StockInventoryRequest(BaseModel):
    """Set stock to specific amount (inventory correction)."""

    product_id: UUID
    new_amount: Decimal = Field(..., ge=0)
    location_id: UUID | None = None
    best_before_date: date | None = None


class StockOpenRequest(BaseModel):
    """Mark stock entry as opened."""

    stock_entry_id: UUID
    amount: Decimal | None = None  # If None, opens entire entry


class StockEntryEditRequest(BaseModel):
    """Edit stock entry (partial)."""

    amount: Decimal | None = Field(None, ge=0)
    best_before_date: date | None = None
    location_id: UUID | None = None
    price: Decimal | None = None
    note: str | None = None
    open: bool | None = None


class StockResponse(BaseModel):
    """Stock response."""

    id: UUID
    tenant_id: UUID
    product_id: UUID
    location_id: UUID | None
    quantity: Decimal
    expiration_date: date | None
    created_at: datetime
    updated_at: datetime
    # Phase 3.5 fields
    stock_id: str | None = None
    purchased_date: date | None = None
    price: Decimal | None = None
    open: bool = False
    opened_date: date | None = None
    note: str | None = None

    model_config = {"from_attributes": True}


class StockEntryResponse(BaseModel):
    """Stock list entry with product and location names (inventory overview)."""

    id: UUID
    product_id: UUID
    product_name: str
    location_id: UUID | None
    location_name: str | None
    quantity: Decimal
    expiration_date: date | None
    created_at: datetime
    updated_at: datetime
    # Phase 3.5 fields
    stock_id: str | None = None
    purchased_date: date | None = None
    price: Decimal | None = None
    open: bool = False
    opened_date: date | None = None
    note: str | None = None


class StockTransactionResponse(BaseModel):
    """Stock transaction response."""

    id: UUID
    tenant_id: UUID
    stock_id: UUID | None
    product_id: UUID | None
    transaction_type: str
    quantity: Decimal
    from_location_id: UUID | None
    to_location_id: UUID | None
    notes: str | None
    spoiled: bool
    correlation_id: UUID | None
    undone: bool
    created_at: datetime

    model_config = {"from_attributes": True}
