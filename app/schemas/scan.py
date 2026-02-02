"""Pydantic schemas for scanning operations."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ScanRequest(BaseModel):
    """Request to scan a barcode."""

    barcode: str = Field(..., min_length=1, max_length=100)
    location_code: str | None = Field(None, description="Location code (e.g., LOC-PANTRY-01)")
    input_method: str = Field("manual", description="How barcode was entered: camera, scanner, manual")


class ProductInfo(BaseModel):
    """Product information from lookup or local cache."""

    name: str | None = None
    brand: str | None = None
    description: str | None = None
    category: str | None = None
    image_url: str | None = None
    quantity: str | None = None
    quantity_unit: str | None = None
    nutrition: dict[str, Any] | None = None
    grocy_product_id: int | None = None
    local_product_id: UUID | None = None
    is_new: bool = True


class ScanResponse(BaseModel):
    """Response from a barcode scan."""

    scan_id: UUID
    barcode: str
    barcode_type: str
    found: bool
    product: ProductInfo | None = None
    location_code: str | None = None
    lookup_provider: str | None = None
    lookup_time_ms: int = 0
    existing_in_grocy: bool = False
    fuzzy_matches: list[ProductInfo] = []


class ScanConfirmRequest(BaseModel):
    """Request to confirm and add a scanned product."""

    name: str = Field(..., min_length=1, max_length=500)
    category: str | None = None
    quantity: int = Field(1, ge=1, le=10000)
    location_code: str | None = None
    best_before: datetime | None = None
    price: float | None = None
    create_in_grocy: bool = True


class ScanConfirmResponse(BaseModel):
    """Response from confirming a scan."""

    success: bool
    product_id: UUID | None = None
    grocy_product_id: int | None = None
    grocy_stock_id: int | None = None
    message: str
