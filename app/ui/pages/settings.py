"""Settings page UI."""

from nicegui import ui

from app.config import settings
from app.ui.layout import create_header, create_mobile_nav


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
            # Grocy settings
            with ui.tab_panel(grocy_tab):
                with ui.card().classes("w-full"):
                    ui.label("Grocy Connection").classes("font-semibold mb-4")

                    ui.input(
                        label="API URL",
                        value=settings.grocy_api_url,
                    ).classes("w-full mb-2")

                    ui.input(
                        label="API Key",
                        value="••••••••",
                        password=True,
                    ).classes("w-full mb-2")

                    ui.input(
                        label="Web URL",
                        value=settings.grocy_web_url,
                    ).classes("w-full mb-4")

                    with ui.row().classes("gap-2"):
                        ui.button("Test Connection", on_click=lambda: None).props("outline")
                        ui.button("Save", on_click=lambda: None).props("color=primary")

            # LLM settings
            with ui.tab_panel(llm_tab):
                with ui.card().classes("w-full"):
                    ui.label("LLM Configuration").classes("font-semibold mb-4")

                    ui.select(
                        ["OpenAI", "Anthropic", "Ollama", "Generic"],
                        value=settings.llm_provider_preset.title(),
                        label="Provider Preset",
                    ).classes("w-full mb-2")

                    ui.input(
                        label="API URL",
                        value=settings.llm_api_url,
                    ).classes("w-full mb-2")

                    ui.input(
                        label="Model",
                        value=settings.llm_model,
                    ).classes("w-full mb-4")

                    ui.button("Save", on_click=lambda: None).props("color=primary")

            # Lookup settings
            with ui.tab_panel(lookup_tab):
                with ui.card().classes("w-full"):
                    ui.label("Lookup Providers").classes("font-semibold mb-4")

                    ui.label("Drag to reorder priority").classes("text-gray-500 text-sm mb-2")

                    # Provider list (placeholder for drag-and-drop)
                    for provider in settings.provider_list:
                        with ui.row().classes("w-full items-center gap-2 p-2 border rounded mb-2"):
                            ui.icon("drag_indicator", color="gray")
                            ui.label(provider.title())
                            ui.space()
                            ui.switch(value=True)

                    ui.button("Save Order", on_click=lambda: None).props("color=primary")

            # Scanning settings
            with ui.tab_panel(scanning_tab):
                with ui.card().classes("w-full"):
                    ui.label("Scanning Behavior").classes("font-semibold mb-4")

                    ui.switch("Auto-add on scan", value=settings.auto_add_enabled)
                    ui.switch("Kiosk mode", value=settings.kiosk_mode_enabled)

                    ui.number(
                        label="Fuzzy match threshold",
                        value=settings.fuzzy_match_threshold,
                        min=0.5,
                        max=1.0,
                        step=0.05,
                    ).classes("w-full mt-4")

                    ui.button("Save", on_click=lambda: None).props("color=primary mt-4")

            # UI settings
            with ui.tab_panel(ui_tab):
                with ui.card().classes("w-full"):
                    ui.label("UI Preferences").classes("font-semibold mb-4")

                    ui.label("Theme")
                    with ui.row().classes("gap-2 mb-4"):
                        ui.button("Light", on_click=lambda: ui.dark_mode().disable()).props(
                            "outline"
                        )
                        ui.button("Dark", on_click=lambda: ui.dark_mode().enable()).props(
                            "outline"
                        )
                        ui.button("Auto", on_click=lambda: ui.dark_mode().auto()).props(
                            "outline"
                        )

    create_mobile_nav()
