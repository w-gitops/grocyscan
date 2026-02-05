"""QR token schemas (Phase 4)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class QrTokenCreate(BaseModel):
    """Create QR token (generate new)."""

    namespace: str = Field(..., min_length=1, max_length=50)


class QrTokenAssign(BaseModel):
    """Assign token to entity."""

    entity_type: str = Field(..., min_length=1, max_length=50)  # product, location, instance
    entity_id: UUID = Field(...)


class QrTokenResponse(BaseModel):
    """QR token response."""

    id: UUID
    tenant_id: UUID
    namespace: str
    code: str
    checksum: str | None
    state: str
    entity_type: str | None
    entity_id: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}
