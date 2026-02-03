"""Device schemas for API v2 (Phase 3)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DeviceCreate(BaseModel):
    """Register device request."""

    name: str = Field(..., min_length=1, max_length=100)
    fingerprint: str = Field(..., min_length=1, max_length=255)
    device_type: str = Field(..., min_length=1, max_length=50)


class DeviceUpdatePreferences(BaseModel):
    """Update device preferences (partial)."""

    default_location_id: UUID | None = None
    default_action: str | None = Field(None, max_length=50)
    scanner_mode: str | None = Field(None, max_length=50)
    preferences: dict | None = None


class DeviceResponse(BaseModel):
    """Device response."""

    id: UUID
    tenant_id: UUID
    user_id: UUID | None
    name: str
    fingerprint: str
    device_type: str
    default_location_id: UUID | None
    default_action: str
    scanner_mode: str
    preferences: dict | None
    last_seen_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
