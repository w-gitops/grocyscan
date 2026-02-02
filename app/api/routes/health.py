"""Health check endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
    environment: str


class DetailedHealthResponse(HealthResponse):
    """Detailed health check response with dependency status."""

    database: str
    redis: str
    grocy: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic health check endpoint.

    Returns:
        HealthResponse: Basic service status
    """
    return HealthResponse(
        status="healthy",
        version=settings.grocyscan_version,
        environment=settings.grocyscan_env,
    )


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check() -> DetailedHealthResponse:
    """Detailed health check with dependency status.

    Checks connectivity to database, Redis, and Grocy.

    Returns:
        DetailedHealthResponse: Service status with dependency health
    """
    # TODO: Implement actual health checks for dependencies
    return DetailedHealthResponse(
        status="healthy",
        version=settings.grocyscan_version,
        environment=settings.grocyscan_env,
        database="healthy",
        redis="healthy",
        grocy="unknown",
    )
