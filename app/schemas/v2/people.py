"""People (household profile) schemas for API v2."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PersonCreate(BaseModel):
    """Create person request."""

    name: str = Field(..., min_length=1, max_length=100)
    nickname: str | None = Field(None, max_length=50)
    avatar_url: str | None = Field(None, max_length=1000)
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    dietary_restrictions: list[str] | None = None
    allergies: list[str] | None = None
    user_id: UUID | None = None
    is_active: bool = True


class PersonUpdate(BaseModel):
    """Update person request (partial)."""

    name: str | None = Field(None, min_length=1, max_length=100)
    nickname: str | None = Field(None, max_length=50)
    avatar_url: str | None = Field(None, max_length=1000)
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    dietary_restrictions: list[str] | None = None
    allergies: list[str] | None = None
    user_id: UUID | None = None
    is_active: bool | None = None


class PersonResponse(BaseModel):
    """Person response."""

    id: UUID
    tenant_id: UUID
    user_id: UUID | None
    name: str
    nickname: str | None
    avatar_url: str | None
    color: str | None
    dietary_restrictions: list[str] | None
    allergies: list[str] | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
