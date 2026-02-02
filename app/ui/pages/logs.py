"""Logs page UI."""

import json
from typing import TYPE_CHECKING

import httpx
from nicegui import ui

from app.config import settings
from app.ui.layout import create_header, create_mobile_nav

if TYPE_CHECKING:
    from fastapi import Request

API_BASE = f"http://localhost:{settings.grocyscan_port}/api"


async def fetch_logs(
    request: "Request | None" = None,
) -> tuple[list[str], str | None, str | None]:
    """Fetch log lines from the API. Returns (lines, error_message, log_file_path)."""
    session_id = request.cookies.get("session_id") if request else None
    cookies = {"session_id": session_id} if session_id else {}
    try:
        async with httpx.AsyncClient(timeout=10, cookies=cookies) as client:
            response = await client.get(f"{API_BASE}/logs")
            if response.status_code == 401:
                return [], "Authentication required. Please log in.", None
            if response.status_code != 200:
                return [], f"API returned {response.status_code}", None
            data = response.json()
            lines = data.get("lines", [])
            message = data.get("message")
            log_file = data.get("log_file")
            return lines, message, log_file
    except Exception as e:
        return [], str(e), None


async def render(request: "Request | None" = None) -> None:
    """Render the logs page."""
    create_header()

    with ui.column().classes("w-full max-w-6xl mx-auto p-4"):
        ui.label("Application Logs").classes("text-2xl font-bold mb-4")

        # Restart hint and log file path (updated when logs load)
        restart_hint = ui.column().classes("w-full mb-2 text-sm text-gray-500")

        with ui.row().classes("w-full gap-4 mb-4"):
            ui.select(
                ["All Levels", "DEBUG", "INFO", "WARNING", "ERROR"],
                value="All Levels",
                label="Level",
            ).classes("w-40")

            ui.input(placeholder="Search logs...").props('prepend-icon="search"').classes("flex-grow")

            def _escape(s: str) -> str:
                return (
                    s.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;")
                )

            current_log_text: list[str] = [""]

            async def load_logs() -> None:
                lines, message, log_file = await fetch_logs(request)
                # Update restart hint and log file path
                restart_hint.clear()
                with restart_hint:
                    if log_file:
                        ui.label(f"Log file: {log_file}").classes("font-mono text-xs")
                    ui.label(
                        "A service restart is shown by 'Starting GrocyScan' and "
                        "'Job queue worker started' entries."
                    ).classes("text-gray-500")
                log_container.clear()
                with log_container:
                    with ui.card().classes("w-full"):
                        with ui.scroll_area().classes("h-96 font-mono text-sm"):
                            if message:
                                current_log_text[0] = message
                                ui.label(message).classes(
                                    "text-amber-600 p-4 whitespace-pre-wrap"
                                )
                            elif not lines:
                                current_log_text[0] = ""
                                ui.label("No log entries.").classes(
                                    "text-gray-500 text-center py-8"
                                )
                            else:
                                current_log_text[0] = "\n".join(lines)
                                ui.html(
                                    "<pre class='p-2 m-0 text-xs overflow-x-auto'>"
                                    + "\n".join(_escape(line) for line in lines)
                                    + "</pre>",
                                    sanitize=False,
                                )

            def copy_all() -> None:
                text = current_log_text[0]
                if not text:
                    ui.notify("Nothing to copy", type="warning")
                    return
                ui.run_javascript(
                    f"navigator.clipboard.writeText({json.dumps(text)}).then(() => true)"
                )
                ui.notify("Copied to clipboard")

            async def clear_log_file() -> None:
                session_id = request.cookies.get("session_id") if request else None
                cookies = {"session_id": session_id} if session_id else {}

                async def on_confirm_clear() -> None:
                    try:
                        async with httpx.AsyncClient(timeout=10, cookies=cookies) as client:
                            r = await client.post(f"{API_BASE}/logs/clear")
                            if r.status_code == 200:
                                ui.notify("Log file cleared.")
                                clear_dialog.close()
                                await load_logs()
                            else:
                                ui.notify(
                                    r.json().get("detail", str(r.status_code)),
                                    type="negative",
                                )
                    except Exception as e:
                        ui.notify(str(e), type="negative")

                with ui.dialog() as clear_dialog, ui.card():
                    ui.label("Clear the entire log file? This cannot be undone.")
                    with ui.row():
                        ui.button("Cancel", on_click=clear_dialog.close).props("outline")
                        ui.button(
                            "Clear log file",
                            on_click=on_confirm_clear,
                        ).props("color=negative")
                clear_dialog.open()

            ui.button("Refresh", icon="refresh", on_click=load_logs).props("outline")
            ui.button("Copy All", icon="content_copy", on_click=copy_all).props("outline")
            ui.button("Clear log file", icon="delete_sweep", on_click=clear_log_file).props(
                "outline color=orange"
            )

        # Container for log content so we can refresh it
        log_container = ui.column().classes("w-full")

        # Initial load
        await load_logs()

    create_mobile_nav()
