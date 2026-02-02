"""Settings management endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.logging import get_logger
from app.services.settings import (
    AllSettings,
    GrocySettings,
    LLMSettings,
    LookupSettings,
    ScanningSettings,
    UISettings,
    settings_service,
)

logger = get_logger(__name__)

router = APIRouter()


class SettingsUpdateRequest(BaseModel):
    """Request to update a settings section."""
    
    values: dict[str, Any]


class SettingsResponse(BaseModel):
    """Response containing settings."""
    
    success: bool
    data: dict[str, Any]
    message: str = ""


@router.get("", response_model=SettingsResponse)
async def get_settings() -> SettingsResponse:
    """Get all current settings.

    Returns:
        SettingsResponse: All settings (with sensitive values masked)
    """
    try:
        settings = settings_service.load()
        data = settings.model_dump()
        
        # Mask sensitive values in response
        _mask_sensitive(data)
        
        return SettingsResponse(
            success=True,
            data=data,
        )
    except Exception as e:
        logger.error("Failed to get settings", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{section}", response_model=SettingsResponse)
async def get_settings_section(section: str) -> SettingsResponse:
    """Get a specific settings section.

    Args:
        section: Section name (llm, lookup, grocy, scanning, ui)

    Returns:
        SettingsResponse: Section settings
    """
    try:
        settings_section = settings_service.get_section(section)
        data = settings_section.model_dump()
        
        # Mask sensitive values in response
        _mask_sensitive_flat(data)
        
        return SettingsResponse(
            success=True,
            data=data,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to get settings section", section=section, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{section}", response_model=SettingsResponse)
async def update_settings_section(
    section: str, request: SettingsUpdateRequest
) -> SettingsResponse:
    """Update a specific settings section.

    Args:
        section: Section name (llm, lookup, grocy, scanning, ui)
        request: Values to update

    Returns:
        SettingsResponse: Updated settings
    """
    try:
        settings = settings_service.update_section(section, request.values)
        data = settings.model_dump()
        
        # Mask sensitive values in response
        _mask_sensitive(data)
        
        logger.info("Settings updated", section=section)
        
        # Hot-reload relevant services based on section
        if section == "lookup":
            _reload_lookup_providers()
        
        return SettingsResponse(
            success=True,
            data=data,
            message=f"{section.title()} settings saved successfully",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to update settings", section=section, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


def _reload_lookup_providers() -> None:
    """Reload lookup providers with new settings."""
    try:
        from app.services.lookup import lookup_manager
        lookup_manager.reload()
        logger.info("Lookup providers reloaded")
    except Exception as e:
        logger.warning("Failed to reload lookup providers", error=str(e))


@router.post("/reset", response_model=SettingsResponse)
async def reset_settings() -> SettingsResponse:
    """Reset all settings to defaults.

    Returns:
        SettingsResponse: Default settings
    """
    try:
        settings = settings_service.reset_to_defaults()
        data = settings.model_dump()
        _mask_sensitive(data)
        
        logger.info("Settings reset to defaults")
        
        return SettingsResponse(
            success=True,
            data=data,
            message="Settings reset to defaults",
        )
    except Exception as e:
        logger.error("Failed to reset settings", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


def _mask_sensitive(data: dict[str, Any]) -> None:
    """Mask sensitive values in settings data."""
    sensitive_keys = {"api_key", "goupc_api_key", "upcitemdb_api_key", "brave_api_key"}
    
    for section in data.values():
        if isinstance(section, dict):
            _mask_sensitive_flat(section)


def _mask_sensitive_flat(data: dict[str, Any]) -> None:
    """Mask sensitive values in a flat dict."""
    sensitive_keys = {"api_key", "goupc_api_key", "upcitemdb_api_key", "brave_api_key"}
    
    for key in sensitive_keys:
        if key in data and data[key]:
            # Show that a value is set but don't reveal it
            data[key] = "••••••••" if data[key] else ""
