"""Label schemas (Phase 4)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LabelTemplateCreate(BaseModel):
    """Create label template."""

    name: str = Field(..., min_length=1, max_length=255)
    template_type: str = Field(..., min_length=1, max_length=50)
    schema_: dict | None = Field(None, alias="schema")


class LabelPreviewRequest(BaseModel):
    """Request label preview (template + variables)."""

    template_id: UUID | None = None
    template_type: str | None = Field(None, max_length=50)
    variables: dict = Field(default_factory=dict)


class LabelPrintRequest(BaseModel):
    """Request print label."""

    template_id: UUID | None = None
    template_type: str | None = Field(None, max_length=50)
    variables: dict = Field(default_factory=dict)


class LabelTemplateResponse(BaseModel):
    """Label template response."""

    id: UUID
    tenant_id: UUID
    name: str
    template_type: str
    template_schema: dict | None = Field(None, alias="schema")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}
