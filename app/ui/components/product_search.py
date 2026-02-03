"""Product name search component for NiceGUI."""

import asyncio
import inspect
from typing import Any, Callable, Coroutine, Union

import httpx
from nicegui import ui

from app.config import settings


class ProductSearchResult:
    """Result item from product search (plain dataclass-style)."""

    def __init__(
        self,
        id: str,
        name: str,
        category: str | None = None,
        image_url: str | None = None,
        source: str = "grocy",
        grocy_product_id: int | None = None,
        barcode: str | None = None,
        nutrition: dict | None = None,
    ) -> None:
        self.id = id
        self.name = name
        self.category = category
        self.image_url = image_url
        self.source = source
        self.grocy_product_id = grocy_product_id
        self.barcode = barcode
        self.nutrition = nutrition


class ProductSearch:
    """Product search component with debounced input and results list.

    search_mode: "grocy" = search Grocy inventory only;
                 "internet" = search external providers (OpenFoodFacts, Brave).
    """

    def __init__(
        self,
        on_select: Callable[
            [ProductSearchResult], Union[None, Coroutine[Any, Any, None]]
        ],
        debounce_ms: int = 300,
        search_mode: str = "grocy",
    ) -> None:
        self.on_select = on_select
        self.debounce_ms = debounce_ms
        self.search_mode = search_mode  # "grocy" or "internet"
        self._input: ui.input | None = None
        self._results_container: ui.column | None = None
        self._search_task: asyncio.Task | None = None
        self._base_url = f"http://localhost:{settings.grocyscan_port}"

    def render(self) -> None:
        """Render the search component."""
        with ui.column().classes("w-full gap-2"):
            self._input = ui.input(
                label="Product Name",
                placeholder="Search products...",
                on_change=self._handle_input_change,
            ).classes("w-full").props('clearable prepend-icon="search"')

            self._results_container = ui.column().classes("w-full gap-1")

            with self._results_container:
                ui.label("Type at least 2 characters to search").classes(
                    "text-gray-500 text-sm"
                )

    async def _handle_input_change(self, e: Any) -> None:
        """Handle search input changes with debouncing."""
        if self._search_task and not self._search_task.done():
            self._search_task.cancel()
        query = ""
        if self._input and self._input.value is not None:
            query = self._input.value.strip()

        if len(query) < 2:
            self._show_minimum_chars_message()
            return

        self._search_task = asyncio.create_task(
            self._debounced_search(query)
        )

    async def _debounced_search(self, query: str) -> None:
        """Execute search after debounce delay."""
        await asyncio.sleep(self.debounce_ms / 1000)
        await self._execute_search(query)

    async def _execute_search(self, query: str) -> None:
        """Execute the product search API call (Grocy or internet based on search_mode)."""
        self._show_loading()

        try:
            async with httpx.AsyncClient(timeout=30 if self.search_mode == "internet" else 10) as client:
                if self.search_mode == "internet":
                    response = await client.post(
                        f"{self._base_url}/api/lookup/search-by-name",
                        json={"query": query, "limit": 20},
                    )
                else:
                    response = await client.post(
                        f"{self._base_url}/api/products/search",
                        json={
                            "query": query,
                            "include_grocy": True,
                            "limit": 20,
                        },
                    )
                response.raise_for_status()
                data = response.json()
            results = data.get("results", [])
            self._display_results(query, results)
        except Exception as e:
            self._show_error(str(e))

    def _display_results(self, query: str, results: list[dict]) -> None:
        """Display search results."""
        if not self._results_container:
            return
        self._results_container.clear()

        if not results:
            with self._results_container:
                with ui.card().classes("w-full p-4"):
                    ui.label(f'No products found matching "{query}"').classes(
                        "text-gray-600"
                    )
                    ui.label(
                        "Try a different search term or scan the barcode instead."
                    ).classes("text-gray-500 text-sm")
            return

        with self._results_container:
            ui.label(f"Search Results ({len(results)} found)").classes(
                "text-sm text-gray-600 font-medium"
            )

            for r in results:
                self._render_result_card(r)

    def _render_result_card(self, result: dict) -> None:
        """Render a single search result card."""
        with ui.card().classes(
            "w-full cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
        ).on("click", lambda r=result: self._handle_select(r)):
            with ui.row().classes("w-full items-center gap-3 p-2"):
                if result.get("image_url"):
                    ui.image(result["image_url"]).classes(
                        "w-12 h-12 object-cover rounded"
                    )
                else:
                    with ui.element("div").classes(
                        "w-12 h-12 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center"
                    ):
                        ui.icon("inventory_2").classes("text-gray-400")

                with ui.column().classes("flex-grow gap-0"):
                    ui.label(result.get("name", "")).classes("font-medium")
                    with ui.row().classes("gap-2 text-sm text-gray-500"):
                        if result.get("category"):
                            ui.label(str(result["category"]))
                            ui.label("•")
                        ui.label(f"From: {(result.get('source') or 'grocy').title()}")

                ui.button(
                    icon="add",
                    on_click=lambda r=result: self._handle_select(r),
                ).props("flat round color=primary")

    async def _handle_select(self, result: dict) -> None:
        """Handle product selection."""
        obj = ProductSearchResult(
            id=str(result.get("id", "")),
            name=result.get("name", ""),
            category=result.get("category"),
            image_url=result.get("image_url"),
            source=result.get("source", "grocy"),
            grocy_product_id=result.get("grocy_product_id"),
            barcode=result.get("barcode"),
            nutrition=result.get("nutrition"),
        )
        callback_result = self.on_select(obj)
        if inspect.iscoroutine(callback_result):
            await callback_result

    def _show_loading(self) -> None:
        """Show loading state."""
        if not self._results_container:
            return
        self._results_container.clear()
        with self._results_container:
            with ui.row().classes("w-full justify-center p-4"):
                ui.spinner()
                ui.label("Searching...").classes("ml-2")

    def _show_minimum_chars_message(self) -> None:
        """Show minimum characters message."""
        if not self._results_container:
            return
        self._results_container.clear()
        with self._results_container:
            ui.label("Type at least 2 characters to search").classes(
                "text-gray-500 text-sm"
            )

    def _show_error(self, message: str) -> None:
        """Show error message."""
        if not self._results_container:
            return
        self._results_container.clear()
        with self._results_container:
            ui.label(f"Search error: {message}").classes("text-red-500")
