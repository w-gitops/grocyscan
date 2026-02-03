"""Logs page UI."""

import json
import re
from typing import TYPE_CHECKING

import httpx
from nicegui import ui

from app.config import settings
from app.ui.layout import create_header, create_mobile_nav

if TYPE_CHECKING:
    from fastapi import Request

API_BASE = f"http://localhost:{settings.grocyscan_port}/api"

# Match structlog-style level in brackets: [info     ] or [ERROR] or "level":"info" (JSON)
_LEVEL_RE = re.compile(
    r"\[(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*\]|\"level\"\s*:\s*\"(debug|info|warning|error|critical)\"",
    re.IGNORECASE,
)
# Match padded level bracket so we can strip it from the display (removes "[info     ] " etc.)
_LEVEL_BRACKET_RE = re.compile(r"\[\s*(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*\]\s*", re.IGNORECASE)

# Badge label for display
_LEVEL_BADGE: dict[str, str] = {
    "debug": "DEBUG",
    "info": "INFO",
    "warning": "WARNING",
    "error": "ERROR",
    "critical": "CRITICAL",
}


def _detect_level(line: str) -> str:
    """Detect log level from a line. Returns lowercase level name or 'info' as default."""
    m = _LEVEL_RE.search(line)
    if m:
        level = (m.group(1) or m.group(2) or "").lower()
        if level in ("debug", "info", "warning", "error", "critical"):
            return level
    return "info"


def _strip_level_bracket(line: str) -> str:
    """Remove the padded '[level     ]' part from the line so display is clean."""
    return _LEVEL_BRACKET_RE.sub("", line, count=1).strip()


# Match leading ISO timestamp (e.g. 2026-02-02T23:56:37.003494Z)
_TIMESTAMP_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T[\d:.]+Z)\s*")


def _split_timestamp(line: str) -> tuple[str, str]:
    """Split line into (timestamp, rest). Returns ('', line) if no timestamp."""
    m = _TIMESTAMP_RE.match(line)
    if m:
        return m.group(1), line[m.end() :].strip()
    return "", line


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

    with ui.column().classes("w-full max-w-6xl mx-auto p-4 md:p-6 gap-4"):
        ui.label("Application Logs").classes("text-2xl font-bold")

        # Level-colored log viewer styles + pill badges + terminal-style panel
        ui.html(
            "<style>"
            ".log-viewer { "
            "  background: #0f172a; border-radius: 0.5rem; "
            "  border: 1px solid rgba(148, 163, 184, 0.2); "
            "  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; "
            "  font-size: 0.8125rem; line-height: 1.5; "
            "}"
            ".log-viewer pre { "
            "  margin: 0; padding: 1rem 1.25rem; "
            "  overflow-x: auto; overflow-y: auto; "
            "  min-height: 24rem; max-height: 70vh; "
            "}"
            ".log-row { "
            "  display: flex; align-items: flex-start; gap: 0.5rem; "
            "  padding: 0.2rem 0; white-space: pre-wrap; word-break: break-all; "
            "}"
            ".log-badge { "
            "  display: inline-block; flex-shrink: 0; "
            "  padding: 0.15rem 0.5rem; border-radius: 9999px; "
            "  font-size: 0.65rem; font-weight: 700; letter-spacing: 0.04em; "
            "  text-align: center; min-width: 4.25rem; "
            "}"
            ".log-badge-debug { background: #475569; color: #e2e8f0; }"
            ".log-badge-info { background: #16a34a; color: white; }"
            ".log-badge-warning { background: #ca8a04; color: #1e293b; }"
            ".log-badge-error { background: #dc2626; color: white; }"
            ".log-badge-critical { background: #7f1d1d; color: #fecaca; }"
            ".log-ts { color: #64748b; flex-shrink: 0; }"
            ".log-msg { color: #cbd5e1; flex: 1; min-width: 0; }"
            ".log-viewer-header { "
            "  padding: 0.5rem 1rem; border-bottom: 1px solid rgba(148, 163, 184, 0.15); "
            "  font-size: 0.75rem; color: #94a3b8; "
            "}"
            "</style>",
            sanitize=False,
        )

        # Restart hint and log file path (updated when logs load)
        restart_hint = ui.column().classes("w-full text-sm text-gray-500 dark:text-gray-400")

        with ui.row().classes("w-full flex-wrap gap-3 items-end"):
            level_select = ui.select(
                ["All Levels", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                value="All Levels",
                label="Level",
            ).classes("w-36")

            search_input = ui.input(
                placeholder="Search logs..."
            ).props('prepend-icon="search"').classes("flex-grow min-w-40")

            def _escape(s: str) -> str:
                return (
                    s.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;")
                )

            def _render_log_line(line: str) -> str:
                level = _detect_level(line)
                badge_text = _LEVEL_BADGE.get(level, "INFO")
                stripped = _strip_level_bracket(line)
                ts, rest = _split_timestamp(stripped)
                msg_part = _escape(rest) if rest else _escape(stripped) if stripped else _escape(line)
                ts_part = f'<span class="log-ts">{_escape(ts)}</span>' if ts else ""
                return (
                    f'<div class="log-row">'
                    f"{ts_part}"
                    f'<span class="log-badge log-badge-{level}">{badge_text}</span>'
                    f'<span class="log-msg">{msg_part}</span>'
                    f"</div>"
                )

            current_log_text: list[str] = [""]

            async def load_logs() -> None:
                lines, message, log_file = await fetch_logs(request)
                # Filter by selected level
                selected_level = level_select.value or "All Levels"
                if lines and selected_level != "All Levels":
                    want = selected_level.lower()
                    lines = [ln for ln in lines if _detect_level(ln) == want]

                # Update restart hint and log file path
                restart_hint.clear()
                with restart_hint:
                    if log_file:
                        ui.label(f"Log file: {log_file}").classes("font-mono text-xs")
                    ui.label(
                        "A service restart is shown by 'Starting GrocyScan' and "
                        "'Job queue worker started' entries."
                    ).classes("text-gray-500")
                    ui.label(
                        "Note: 'Request is not set' in logs is a known NiceGUI startup "
                        "message and can be ignored."
                    ).classes("text-gray-400 text-xs mt-1")
                # Optional search filter
                search_term = (search_input.value or "").strip().lower()
                if lines and search_term:
                    lines = [ln for ln in lines if search_term in ln.lower()]

                log_container.clear()
                with log_container:
                    if message:
                        current_log_text[0] = message
                        with ui.card().classes("w-full border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/30"):
                            ui.label(message).classes(
                                "text-amber-700 dark:text-amber-400 p-4 whitespace-pre-wrap text-sm"
                            )
                    elif not lines:
                        current_log_text[0] = ""
                        with ui.card().classes("w-full"):
                            ui.label("No log entries.").classes(
                                "text-gray-500 text-center py-12"
                            )
                    else:
                        current_log_text[0] = "\n".join(lines)
                        colored = "\n".join(_render_log_line(ln) for ln in lines)
                        line_count = len(lines)
                        ui.html(
                            f'<div class="log-viewer">'
                            f'<div class="log-viewer-header">'
                            f'Last {line_count} line{"s" if line_count != 1 else ""}'
                            f'</div><pre>{colored}</pre></div>',
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

            level_select.on_value_change(load_logs)

            ui.element("div").classes("flex-grow")
            ui.button("Refresh", icon="refresh", on_click=load_logs).props("outline")
            ui.button("Copy", icon="content_copy", on_click=copy_all).props("outline")
            ui.button("Clear", icon="delete_sweep", on_click=clear_log_file).props(
                "outline color=orange"
            )

        # Container for log content so we can refresh it
        log_container = ui.column().classes("w-full")

        # Initial load
        await load_logs()

    create_mobile_nav()
