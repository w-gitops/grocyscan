"""Jobs page UI."""

from nicegui import ui

from app.ui.layout import create_header, create_mobile_nav


async def render() -> None:
    """Render the jobs page."""
    create_header()

    with ui.column().classes("w-full max-w-6xl mx-auto p-4"):
        # Page title
        ui.label("Job Queue").classes("text-2xl font-bold mb-4")

        # Stats cards
        with ui.row().classes("w-full gap-4 mb-4"):
            with ui.card().classes("flex-1"):
                ui.label("Pending").classes("text-gray-500 text-sm")
                ui.label("0").classes("text-2xl font-bold")

            with ui.card().classes("flex-1"):
                ui.label("Running").classes("text-gray-500 text-sm")
                ui.label("0").classes("text-2xl font-bold text-blue-500")

            with ui.card().classes("flex-1"):
                ui.label("Failed").classes("text-gray-500 text-sm")
                ui.label("0").classes("text-2xl font-bold text-red-500")

            with ui.card().classes("flex-1"):
                ui.label("Completed").classes("text-gray-500 text-sm")
                ui.label("0").classes("text-2xl font-bold text-green-500")

        # Filter
        with ui.row().classes("w-full gap-4 mb-4"):
            ui.select(
                ["All", "Pending", "Running", "Completed", "Failed"],
                value="All",
                label="Status",
            ).classes("w-48")

        # Jobs table placeholder
        with ui.card().classes("w-full"):
            ui.label("Job queue will be displayed here with AG Grid").classes(
                "text-gray-500 text-center py-8"
            )

    create_mobile_nav()
