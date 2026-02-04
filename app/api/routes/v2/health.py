"""Health check for API v2 (Phase 1: GET /health returns 200)."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health response."""

    status: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check. GET /health returns 200."""
    return HealthResponse(
        status="healthy",
        version=settings.grocyscan_version,
    )
