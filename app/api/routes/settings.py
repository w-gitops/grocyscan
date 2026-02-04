"""Settings management endpoints."""

from typing import Any

import httpx
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
    sensitive_keys = {
        "api_key",
        "goupc_api_key",
        "upcitemdb_api_key",
        "brave_api_key",
        "password_hash",
    }
    
    for section in data.values():
        if isinstance(section, dict):
            _mask_sensitive_flat(section)


def _mask_sensitive_flat(data: dict[str, Any]) -> None:
    """Mask sensitive values in a flat dict."""
    sensitive_keys = {
        "api_key",
        "goupc_api_key",
        "upcitemdb_api_key",
        "brave_api_key",
        "password_hash",
    }
    
    for key in sensitive_keys:
        if key in data and data[key]:
            # Show that a value is set but don't reveal it
            data[key] = "••••••••" if data[key] else ""


class ModelsResponse(BaseModel):
    """Response containing available models."""
    
    success: bool
    models: list[str]
    provider: str
    message: str = ""


@router.get("/llm/models", response_model=ModelsResponse)
async def get_available_models() -> ModelsResponse:
    """Fetch available models from the configured LLM provider.
    
    Returns:
        ModelsResponse: List of available model names
    """
    try:
        llm_settings = settings_service.get_section("llm")
        api_url = llm_settings.api_url
        api_key = llm_settings.api_key
        provider = llm_settings.provider_preset
        
        models = await _fetch_models_from_provider(api_url, api_key, provider)
        
        return ModelsResponse(
            success=True,
            models=models,
            provider=provider,
        )
    except Exception as e:
        logger.error("Failed to fetch models", error=str(e))
        return ModelsResponse(
            success=False,
            models=[],
            provider="unknown",
            message=str(e),
        )


async def _fetch_models_from_provider(
    api_url: str, api_key: str, provider: str
) -> list[str]:
    """Fetch available models from a provider's API.
    
    Args:
        api_url: Provider API base URL
        api_key: API key for authentication
        provider: Provider name (openai, anthropic, ollama, generic)
        
    Returns:
        List of model names
    """
    models = []
    headers = {}
    
    # Set up auth headers
    if api_key:
        if provider == "anthropic":
            headers["x-api-key"] = api_key
            headers["anthropic-version"] = "2023-06-01"
        else:
            headers["Authorization"] = f"Bearer {api_key}"
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            if provider == "ollama":
                # Ollama uses /api/tags endpoint
                # Convert /v1 style URL to Ollama native
                base_url = api_url.replace("/v1", "")
                response = await client.get(f"{base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [m["name"] for m in data.get("models", [])]
                    
            elif provider == "anthropic":
                # Anthropic doesn't have a models endpoint, return common models
                models = [
                    "claude-3-opus-20240229",
                    "claude-3-sonnet-20240229",
                    "claude-3-haiku-20240307",
                    "claude-3-5-sonnet-20240620",
                    "claude-3-5-sonnet-20241022",
                ]
                
            else:
                # OpenAI-compatible /v1/models endpoint
                response = await client.get(
                    f"{api_url}/models",
                    headers=headers,
                )
                if response.status_code == 200:
                    data = response.json()
                    all_models = [m["id"] for m in data.get("data", [])]
                    
                    # Filter to relevant models for OpenAI
                    if provider == "openai":
                        # Prioritize common models
                        priority_models = [
                            "gpt-4o",
                            "gpt-4o-mini",
                            "gpt-4-turbo",
                            "gpt-4",
                            "gpt-3.5-turbo",
                            "o1-preview",
                            "o1-mini",
                        ]
                        # Add priority models that exist
                        for m in priority_models:
                            if m in all_models:
                                models.append(m)
                        # Add any other gpt/o1 models not in priority list
                        for m in all_models:
                            if (m.startswith("gpt-") or m.startswith("o1-")) and m not in models:
                                models.append(m)
                    else:
                        # For generic providers, return all models
                        models = all_models
                        
        except httpx.ConnectError:
            logger.warning(f"Could not connect to {api_url}")
        except Exception as e:
            logger.warning(f"Error fetching models: {e}")
    
    return models


class ProviderTestResponse(BaseModel):
    """Response from testing a lookup provider."""
    
    success: bool
    provider: str
    message: str
    lookup_time_ms: int = 0
    product_name: str | None = None


class ConnectionTestResponse(BaseModel):
    """Response from testing a connection."""
    
    success: bool
    message: str
    details: dict[str, Any] | None = None


@router.post("/grocy/test", response_model=ConnectionTestResponse)
async def test_grocy_connection() -> ConnectionTestResponse:
    """Test connection to Grocy using stored credentials.
    
    Returns:
        ConnectionTestResponse: Test result with Grocy system info
    """
    try:
        grocy_settings = settings_service.get_section("grocy")
        api_url = grocy_settings.api_url
        api_key = grocy_settings.api_key
        
        if not api_url:
            return ConnectionTestResponse(
                success=False,
                message="Grocy API URL not configured",
            )
        
        if not api_key:
            return ConnectionTestResponse(
                success=False,
                message="Grocy API key not configured",
            )
        
        # Test connection to Grocy
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{api_url}/api/system/info",
                headers={"GROCY-API-KEY": api_key},
            )
            
            if response.status_code == 200:
                data = response.json()
                return ConnectionTestResponse(
                    success=True,
                    message=f"Connected to Grocy {data.get('grocy_version', {}).get('Version', 'unknown')}",
                    details={
                        "version": data.get("grocy_version", {}).get("Version"),
                        "php_version": data.get("php_version"),
                        "sqlite_version": data.get("sqlite_version"),
                    },
                )
            elif response.status_code == 401:
                return ConnectionTestResponse(
                    success=False,
                    message="Authentication failed - check API key",
                )
            else:
                return ConnectionTestResponse(
                    success=False,
                    message=f"HTTP {response.status_code}: {response.text[:100]}",
                )
                
    except httpx.ConnectError:
        return ConnectionTestResponse(
            success=False,
            message="Could not connect to Grocy server",
        )
    except Exception as e:
        logger.error("Grocy connection test failed", error=str(e))
        return ConnectionTestResponse(
            success=False,
            message=str(e),
        )


@router.post("/lookup/test/{provider}", response_model=ProviderTestResponse)
async def test_lookup_provider(provider: str) -> ProviderTestResponse:
    """Test a lookup provider with a known barcode.
    
    Args:
        provider: Provider name (openfoodfacts, goupc, upcitemdb, brave)
        
    Returns:
        ProviderTestResponse: Test result
    """
    # Test barcode - Coca-Cola Classic (widely available in most databases)
    test_barcode = "049000042566"
    
    try:
        # Import provider classes directly to test them independently
        from app.services.lookup.brave import BraveSearchProvider
        from app.services.lookup.goupc import GoUPCProvider
        from app.services.lookup.openfoodfacts import OpenFoodFactsProvider
        from app.services.lookup.upcitemdb import UPCItemDBProvider
        
        # Create provider instance based on name
        provider_classes = {
            "openfoodfacts": OpenFoodFactsProvider,
            "goupc": GoUPCProvider,
            "upcitemdb": UPCItemDBProvider,
            "brave": BraveSearchProvider,
        }
        
        provider_lower = provider.lower()
        if provider_lower not in provider_classes:
            return ProviderTestResponse(
                success=False,
                provider=provider,
                message=f"Unknown provider '{provider}'",
            )
        
        # Create a fresh instance for testing
        provider_instance = provider_classes[provider_lower]()
        
        # Check if enabled
        if not provider_instance.is_enabled():
            return ProviderTestResponse(
                success=False,
                provider=provider,
                message=f"{provider} is disabled in settings",
            )
        
        # Check if API key required but missing
        if hasattr(provider_instance, 'get_api_key'):
            api_key = provider_instance.get_api_key()
            # For providers that need keys, check if set
            # Note: upcitemdb works without key (free tier, 100 req/day)
            if provider_lower in ['goupc', 'brave'] and not api_key:
                return ProviderTestResponse(
                    success=False,
                    provider=provider,
                    message=f"API key not configured for {provider}",
                )
        
        # Perform test lookup
        result = await provider_instance.lookup(test_barcode)
        
        if result.found:
            return ProviderTestResponse(
                success=True,
                provider=provider,
                message=f"Successfully found product",
                lookup_time_ms=result.lookup_time_ms,
                product_name=result.name,
            )
        else:
            return ProviderTestResponse(
                success=False,
                provider=provider,
                message="Provider responded but product not found",
                lookup_time_ms=result.lookup_time_ms,
            )
            
    except Exception as e:
        logger.error(f"Provider test failed", provider=provider, error=str(e))
        return ProviderTestResponse(
            success=False,
            provider=provider,
            message=str(e),
        )
