"""Products page UI."""

from nicegui import ui

from app.ui.layout import create_header, create_mobile_nav


async def render() -> None:
    """Render the products page."""
    create_header()

    with ui.column().classes("w-full max-w-6xl mx-auto p-4"):
        # Page title and actions
        with ui.row().classes("w-full items-center justify-between mb-4"):
            ui.label("Products").classes("text-2xl font-bold")
            ui.button("Add Product", icon="add", on_click=lambda: None).props("color=primary")

        # Search and filter
        with ui.row().classes("w-full gap-4 mb-4"):
            ui.input(placeholder="Search products...", icon="search").classes("flex-grow")
            ui.select(
                ["All Categories", "Groceries", "Dairy", "Produce", "Frozen"],
                value="All Categories",
            ).classes("w-48")

        # Products table placeholder
        with ui.card().classes("w-full"):
            ui.label("Products will be displayed here with AG Grid").classes(
                "text-gray-500 text-center py-8"
            )

    create_mobile_nav()
