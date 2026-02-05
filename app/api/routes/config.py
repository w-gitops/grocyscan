"""Public app config (e.g. product title for UI). No auth required."""

from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("", description="Public app config for frontend (e.g. app title, version)")
async def get_config() -> dict:
    """Return config values the frontend needs (product title, version, etc.)."""
    return {
        "app_title": settings.app_title,
        "version": settings.grocyscan_version,
    }
