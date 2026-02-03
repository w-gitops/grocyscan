"""Location schemas for API v2."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LocationCreate(BaseModel):
    """Create location request."""

    name: str = Field(..., min_length=1, max_length=255)
    location_type: str = Field(..., min_length=1, max_length=50)
    parent_id: UUID | None = None
    description: str | None = None
    sort_order: int = 0
    is_freezer: bool = False


class LocationUpdate(BaseModel):
    """Update location request (partial)."""

    name: str | None = Field(None, min_length=1, max_length=255)
    location_type: str | None = Field(None, max_length=50)
    parent_id: UUID | None = None
    description: str | None = None
    sort_order: int | None = None
    is_freezer: bool | None = None


class LocationResponse(BaseModel):
    """Location response."""

    id: UUID
    tenant_id: UUID
    parent_id: UUID | None
    name: str
    location_type: str
    path: str | None
    description: str | None
    sort_order: int
    is_freezer: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
