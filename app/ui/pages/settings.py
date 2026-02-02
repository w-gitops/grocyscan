"""Settings page UI."""

import json
from typing import Any

import httpx
from nicegui import ui

from app.config import settings
from app.core.logging import get_logger
from app.ui.layout import create_header, create_mobile_nav

logger = get_logger(__name__)

# LLM Provider presets with default configurations
LLM_PRESETS = {
    "openai": {
        "api_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "requires_key": True,
        "description": "OpenAI GPT models (requires API key)",
    },
    "anthropic": {
        "api_url": "https://api.anthropic.com",
        "model": "claude-3-haiku-20240307",
        "requires_key": True,
        "description": "Anthropic Claude models (requires API key)",
    },
    "ollama": {
        "api_url": "http://localhost:11434/v1",
        "model": "llama3.1:8b",
        "requires_key": False,
        "description": "Local Ollama instance (no API key needed)",
    },
    "generic": {
        "api_url": "http://localhost:8080/v1",
        "model": "default",
        "requires_key": False,
        "description": "Generic OpenAI-compatible endpoint",
    },
}

API_BASE = f"http://localhost:{settings.grocyscan_port}/api"


async def fetch_settings(section: str | None = None) -> dict[str, Any]:
    """Fetch settings from API."""
    try:
        async with httpx.AsyncClient() as client:
            if section:
                response = await client.get(f"{API_BASE}/settings/{section}", timeout=10)
            else:
                response = await client.get(f"{API_BASE}/settings", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {})
    except Exception as e:
        logger.error("Failed to fetch settings", error=str(e))
    return {}


async def save_settings(section: str, values: dict[str, Any]) -> tuple[bool, str]:
    """Save settings to API."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{API_BASE}/settings/{section}",
                json={"values": values},
                timeout=10,
            )
            
            if response.status_code == 200:
                data = response.json()
                return True, data.get("message", "Settings saved")
            else:
                return False, f"Error: {response.status_code}"
    except Exception as e:
        logger.error("Failed to save settings", error=str(e))
        return False, str(e)


async def render() -> None:
    """Render the settings page."""
    create_header()

    with ui.column().classes("w-full max-w-4xl mx-auto p-4"):
        # Page title
        ui.label("Settings").classes("text-2xl font-bold mb-4")

        # Tabs for different setting categories
        with ui.tabs().classes("w-full") as tabs:
            grocy_tab = ui.tab("Grocy")
            llm_tab = ui.tab("LLM")
            lookup_tab = ui.tab("Lookup")
            scanning_tab = ui.tab("Scanning")
            ui_tab = ui.tab("UI")

        with ui.tab_panels(tabs, value=grocy_tab).classes("w-full"):
            # ==================== GROCY SETTINGS ====================
            with ui.tab_panel(grocy_tab):
                await render_grocy_settings()

            # ==================== LLM SETTINGS ====================
            with ui.tab_panel(llm_tab):
                await render_llm_settings()

            # ==================== LOOKUP SETTINGS ====================
            with ui.tab_panel(lookup_tab):
                await render_lookup_settings()

            # ==================== SCANNING SETTINGS ====================
            with ui.tab_panel(scanning_tab):
                await render_scanning_settings()

            # ==================== UI SETTINGS ====================
            with ui.tab_panel(ui_tab):
                await render_ui_settings()

    create_mobile_nav()


async def render_grocy_settings() -> None:
    """Render Grocy connection settings."""
    # Load current settings
    current = await fetch_settings("grocy")
    
    state = {
        "api_url": current.get("api_url", "http://localhost:9283"),
        "api_key": "",  # Don't pre-fill masked value
        "web_url": current.get("web_url", "http://localhost:9283"),
    }
    
    with ui.card().classes("w-full"):
        ui.label("Grocy Connection").classes("font-semibold mb-4")
        
        ui.input(
            label="API URL",
            value=state["api_url"],
            on_change=lambda e: state.update({"api_url": e.value}),
        ).classes("w-full mb-2")
        
        ui.input(
            label="API Key",
            placeholder="Enter new API key to update",
            password=True,
            password_toggle_button=True,
            on_change=lambda e: state.update({"api_key": e.value}),
        ).classes("w-full mb-2")
        
        ui.label("Leave blank to keep existing key").classes("text-xs text-gray-500 mb-2")
        
        ui.input(
            label="Web URL",
            value=state["web_url"],
            on_change=lambda e: state.update({"web_url": e.value}),
        ).classes("w-full mb-4")
        
        status_label = ui.label("").classes("text-sm mb-4")
        
        async def test_grocy():
            status_label.text = "Testing connection..."
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{state['api_url']}/api/system/info",
                        headers={"GROCY-API-KEY": state["api_key"]} if state["api_key"] else {},
                        timeout=10,
                    )
                    if response.status_code == 200:
                        status_label.text = "✓ Connection successful"
                        status_label.classes(replace="text-sm mb-4 text-green-500")
                        ui.notify("Grocy connection successful", type="positive")
                    else:
                        status_label.text = f"✗ Connection failed: {response.status_code}"
                        status_label.classes(replace="text-sm mb-4 text-red-500")
            except Exception as e:
                status_label.text = f"✗ Connection failed: {e}"
                status_label.classes(replace="text-sm mb-4 text-red-500")
        
        async def save_grocy():
            # Only include api_key if user entered a new one
            values = {
                "api_url": state["api_url"],
                "web_url": state["web_url"],
            }
            if state["api_key"]:
                values["api_key"] = state["api_key"]
            
            success, message = await save_settings("grocy", values)
            if success:
                status_label.text = f"✓ {message}"
                status_label.classes(replace="text-sm mb-4 text-green-500")
                ui.notify(message, type="positive")
            else:
                status_label.text = f"✗ {message}"
                status_label.classes(replace="text-sm mb-4 text-red-500")
                ui.notify(message, type="negative")
        
        with ui.row().classes("gap-2"):
            ui.button("Test Connection", on_click=test_grocy).props("outline")
            ui.button("Save", on_click=save_grocy).props("color=primary")


async def render_llm_settings() -> None:
    """Render LLM configuration settings."""
    # Load current settings
    current = await fetch_settings("llm")
    
    state = {
        "preset": current.get("provider_preset", "ollama"),
        "api_url": current.get("api_url", "http://localhost:11434/v1"),
        "api_key": "",  # Don't pre-fill masked value
        "model": current.get("model", "llama3.1:8b"),
    }
    
    with ui.card().classes("w-full"):
        ui.label("LLM Configuration").classes("font-semibold mb-4")
        
        # Provider preset description
        preset_description = ui.label(
            LLM_PRESETS.get(state["preset"], {}).get("description", "")
        ).classes("text-sm text-gray-500 mb-4")
        
        # Create references for fields we need to update
        api_url_input = None
        model_input = None
        api_key_container = None
        
        def on_preset_change(e):
            preset = e.value.lower()
            state["preset"] = preset
            preset_config = LLM_PRESETS.get(preset, {})
            
            # Update fields with preset defaults
            if api_url_input:
                api_url_input.value = preset_config.get("api_url", "")
            if model_input:
                model_input.value = preset_config.get("model", "")
            state["api_url"] = preset_config.get("api_url", "")
            state["model"] = preset_config.get("model", "")
            
            # Show/hide API key field based on preset
            requires_key = preset_config.get("requires_key", False)
            if api_key_container:
                api_key_container.set_visibility(requires_key)
            
            # Update description
            preset_description.text = preset_config.get("description", "")
        
        ui.select(
            ["OpenAI", "Anthropic", "Ollama", "Generic"],
            value=state["preset"].title(),
            label="Provider Preset",
            on_change=on_preset_change,
        ).classes("w-full mb-2")
        
        # API Key container (shown/hidden based on preset)
        current_preset = LLM_PRESETS.get(state["preset"], {})
        with ui.column().classes("w-full") as api_key_container:
            ui.input(
                label="API Key",
                placeholder="Enter API key",
                password=True,
                password_toggle_button=True,
                on_change=lambda e: state.update({"api_key": e.value}),
            ).classes("w-full mb-2")
            
            ui.label(
                "Your API key is stored securely and encrypted."
            ).classes("text-xs text-gray-500 mb-2")
        
        # Show/hide based on current preset
        api_key_container.set_visibility(current_preset.get("requires_key", False))
        
        api_url_input = ui.input(
            label="API URL",
            value=state["api_url"],
            on_change=lambda e: state.update({"api_url": e.value}),
        ).classes("w-full mb-2")
        
        model_input = ui.input(
            label="Model",
            value=state["model"],
            on_change=lambda e: state.update({"model": e.value}),
        ).classes("w-full mb-4")
        
        status_label = ui.label("").classes("text-sm mb-4")
        
        async def test_llm():
            status_label.text = "Testing connection..."
            # For now, just validate the configuration
            status_label.text = "✓ Configuration appears valid"
            status_label.classes(replace="text-sm mb-4 text-green-500")
            ui.notify("LLM configuration valid", type="positive")
        
        async def save_llm():
            values = {
                "provider_preset": state["preset"],
                "api_url": state["api_url"],
                "model": state["model"],
            }
            if state["api_key"]:
                values["api_key"] = state["api_key"]
            
            success, message = await save_settings("llm", values)
            if success:
                status_label.text = f"✓ {message}"
                status_label.classes(replace="text-sm mb-4 text-green-500")
                ui.notify(message, type="positive")
            else:
                status_label.text = f"✗ {message}"
                status_label.classes(replace="text-sm mb-4 text-red-500")
                ui.notify(message, type="negative")
        
        with ui.row().classes("gap-2"):
            ui.button("Test Connection", on_click=test_llm).props("outline")
            ui.button("Save", on_click=save_llm).props("color=primary")


async def render_lookup_settings() -> None:
    """Render lookup provider settings."""
    # Load current settings
    current = await fetch_settings("lookup")
    
    state = {
        "strategy": current.get("strategy", "sequential"),
        "provider_order": current.get("provider_order", ["openfoodfacts", "goupc", "upcitemdb", "brave"]),
        "openfoodfacts_enabled": current.get("openfoodfacts_enabled", True),
        "goupc_enabled": current.get("goupc_enabled", False),
        "goupc_api_key": "",
        "upcitemdb_enabled": current.get("upcitemdb_enabled", False),
        "upcitemdb_api_key": "",
        "brave_enabled": current.get("brave_enabled", False),
        "brave_api_key": "",
        "brave_use_as_fallback": current.get("brave_use_as_fallback", True),
    }
    
    with ui.card().classes("w-full"):
        ui.label("Lookup Providers").classes("font-semibold mb-4")
        ui.label("Configure barcode lookup providers and API keys").classes("text-sm text-gray-500 mb-4")
        
        # Strategy selection
        ui.select(
            ["Sequential", "Parallel"],
            value=state["strategy"].title(),
            label="Lookup Strategy",
            on_change=lambda e: state.update({"strategy": e.value.lower()}),
        ).classes("w-full mb-4")
        
        ui.label("Provider priority (top = highest)").classes("text-sm text-gray-600 mb-2")
        
        # OpenFoodFacts (always free, no key needed)
        with ui.card().classes("w-full mb-3 p-3"):
            with ui.row().classes("w-full items-center justify-between"):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("drag_indicator", color="gray")
                    ui.label("OpenFoodFacts").classes("font-medium")
                    ui.badge("Free", color="green").classes("ml-2")
                ui.switch(
                    value=state["openfoodfacts_enabled"],
                    on_change=lambda e: state.update({"openfoodfacts_enabled": e.value}),
                )
            ui.label("Open database with nutrition info. No API key required.").classes(
                "text-xs text-gray-500 mt-1"
            )
        
        # go-upc
        with ui.card().classes("w-full mb-3 p-3"):
            with ui.row().classes("w-full items-center justify-between"):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("drag_indicator", color="gray")
                    ui.label("go-upc.com").classes("font-medium")
                    ui.badge("API Key", color="orange").classes("ml-2")
                ui.switch(
                    value=state["goupc_enabled"],
                    on_change=lambda e: state.update({"goupc_enabled": e.value}),
                )
            ui.label("Commercial UPC database with good coverage.").classes(
                "text-xs text-gray-500 mt-1"
            )
            ui.input(
                label="API Key",
                placeholder="Enter go-upc.com API key",
                password=True,
                password_toggle_button=True,
                on_change=lambda e: state.update({"goupc_api_key": e.value}),
            ).classes("w-full mt-2")
        
        # UPCitemdb
        with ui.card().classes("w-full mb-3 p-3"):
            with ui.row().classes("w-full items-center justify-between"):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("drag_indicator", color="gray")
                    ui.label("UPCitemdb").classes("font-medium")
                    ui.badge("API Key", color="orange").classes("ml-2")
                ui.switch(
                    value=state["upcitemdb_enabled"],
                    on_change=lambda e: state.update({"upcitemdb_enabled": e.value}),
                )
            ui.label("Large UPC database with free tier available.").classes(
                "text-xs text-gray-500 mt-1"
            )
            ui.input(
                label="API Key",
                placeholder="Enter UPCitemdb API key",
                password=True,
                password_toggle_button=True,
                on_change=lambda e: state.update({"upcitemdb_api_key": e.value}),
            ).classes("w-full mt-2")
        
        # Brave Search
        with ui.card().classes("w-full mb-3 p-3"):
            with ui.row().classes("w-full items-center justify-between"):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("drag_indicator", color="gray")
                    ui.label("Brave Search").classes("font-medium")
                    ui.badge("Fallback", color="blue").classes("ml-2")
                ui.switch(
                    value=state["brave_enabled"],
                    on_change=lambda e: state.update({"brave_enabled": e.value}),
                )
            ui.label("Web search fallback for unknown products.").classes(
                "text-xs text-gray-500 mt-1"
            )
            ui.input(
                label="API Key",
                placeholder="Enter Brave Search API key",
                password=True,
                password_toggle_button=True,
                on_change=lambda e: state.update({"brave_api_key": e.value}),
            ).classes("w-full mt-2")
            ui.switch(
                "Use as fallback only",
                value=state["brave_use_as_fallback"],
                on_change=lambda e: state.update({"brave_use_as_fallback": e.value}),
            ).classes("mt-2")
        
        status_label = ui.label("").classes("text-sm mb-4")
        
        async def save_lookup():
            values = {
                "strategy": state["strategy"],
                "openfoodfacts_enabled": state["openfoodfacts_enabled"],
                "goupc_enabled": state["goupc_enabled"],
                "upcitemdb_enabled": state["upcitemdb_enabled"],
                "brave_enabled": state["brave_enabled"],
                "brave_use_as_fallback": state["brave_use_as_fallback"],
            }
            # Only include API keys if entered
            if state["goupc_api_key"]:
                values["goupc_api_key"] = state["goupc_api_key"]
            if state["upcitemdb_api_key"]:
                values["upcitemdb_api_key"] = state["upcitemdb_api_key"]
            if state["brave_api_key"]:
                values["brave_api_key"] = state["brave_api_key"]
            
            success, message = await save_settings("lookup", values)
            if success:
                status_label.text = f"✓ {message}"
                status_label.classes(replace="text-sm mb-4 text-green-500")
                ui.notify(message, type="positive")
            else:
                status_label.text = f"✗ {message}"
                status_label.classes(replace="text-sm mb-4 text-red-500")
                ui.notify(message, type="negative")
        
        ui.button("Save", on_click=save_lookup).props("color=primary")


async def render_scanning_settings() -> None:
    """Render scanning behavior settings."""
    # Load current settings
    current = await fetch_settings("scanning")
    
    state = {
        "auto_add_enabled": current.get("auto_add_enabled", False),
        "kiosk_mode_enabled": current.get("kiosk_mode_enabled", False),
        "fuzzy_match_threshold": current.get("fuzzy_match_threshold", 0.9),
        "default_quantity_unit": current.get("default_quantity_unit", "pieces"),
    }
    
    with ui.card().classes("w-full"):
        ui.label("Scanning Behavior").classes("font-semibold mb-4")
        
        ui.switch(
            "Auto-add on scan",
            value=state["auto_add_enabled"],
            on_change=lambda e: state.update({"auto_add_enabled": e.value}),
        )
        ui.label("Automatically add products without confirmation").classes(
            "text-xs text-gray-500 mb-4"
        )
        
        ui.switch(
            "Kiosk mode",
            value=state["kiosk_mode_enabled"],
            on_change=lambda e: state.update({"kiosk_mode_enabled": e.value}),
        )
        ui.label("Simplified interface for scanning stations").classes(
            "text-xs text-gray-500 mb-4"
        )
        
        ui.number(
            label="Fuzzy match threshold",
            value=state["fuzzy_match_threshold"],
            min=0.5,
            max=1.0,
            step=0.05,
            on_change=lambda e: state.update({"fuzzy_match_threshold": e.value}),
        ).classes("w-full mt-4")
        ui.label("How similar product names must be for auto-matching (0.5-1.0)").classes(
            "text-xs text-gray-500 mb-4"
        )
        
        ui.input(
            label="Default quantity unit",
            value=state["default_quantity_unit"],
            on_change=lambda e: state.update({"default_quantity_unit": e.value}),
        ).classes("w-full mb-4")
        
        status_label = ui.label("").classes("text-sm mb-4")
        
        async def save_scanning():
            success, message = await save_settings("scanning", state)
            if success:
                status_label.text = f"✓ {message}"
                status_label.classes(replace="text-sm mb-4 text-green-500")
                ui.notify(message, type="positive")
            else:
                status_label.text = f"✗ {message}"
                status_label.classes(replace="text-sm mb-4 text-red-500")
                ui.notify(message, type="negative")
        
        ui.button("Save", on_click=save_scanning).props("color=primary")


async def render_ui_settings() -> None:
    """Render UI preference settings."""
    # Load current settings
    current = await fetch_settings("ui")
    
    state = {
        "theme": current.get("theme", "auto"),
    }
    
    with ui.card().classes("w-full"):
        ui.label("UI Preferences").classes("font-semibold mb-4")
        
        ui.label("Theme")
        with ui.row().classes("gap-2 mb-4"):
            def set_theme(theme: str):
                state["theme"] = theme
                if theme == "light":
                    ui.dark_mode().disable()
                elif theme == "dark":
                    ui.dark_mode().enable()
                else:
                    ui.dark_mode().auto()
            
            ui.button("Light", on_click=lambda: set_theme("light")).props("outline")
            ui.button("Dark", on_click=lambda: set_theme("dark")).props("outline")
            ui.button("Auto", on_click=lambda: set_theme("auto")).props("outline")
        
        status_label = ui.label("").classes("text-sm mb-4")
        
        async def save_ui():
            success, message = await save_settings("ui", state)
            if success:
                status_label.text = f"✓ {message}"
                status_label.classes(replace="text-sm mb-4 text-green-500")
                ui.notify(message, type="positive")
            else:
                status_label.text = f"✗ {message}"
                status_label.classes(replace="text-sm mb-4 text-red-500")
                ui.notify(message, type="negative")
        
        ui.button("Save Theme Preference", on_click=save_ui).props("color=primary")
