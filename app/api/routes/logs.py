"""Log viewer endpoints."""

import re
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.core.logging import clear_log_buffer, get_log_buffer_lines, get_logger

router = APIRouter()
logger = get_logger(__name__)

MAX_LINES = 500

# Strip ANSI escape sequences (colors, bold, etc.) so log viewer is readable
_ANSI_ESCAPE = re.compile(r"(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]")


def _strip_ansi(line: str) -> str:
    return _ANSI_ESCAPE.sub("", line)


@router.get("")
async def get_logs() -> dict:
    """Get application logs.

    Reads from the configured log file (LOG_FILE) when set.
    Returns last MAX_LINES lines. When LOG_FILE is not set, returns a message
    explaining how to enable in-app log viewing.

    Returns:
        dict: {"lines": list[str], "message": str | None}
    """
    if not settings.log_file or not settings.log_file.strip():
        buffered = [
            _strip_ansi(line.rstrip("\n\r"))
            for line in get_log_buffer_lines(MAX_LINES)
        ]
        return {
            "lines": buffered,
            "message": (
                f"Log file not configured. Showing in-memory logs (last {MAX_LINES} lines). "
                "Set LOG_FILE in your environment (e.g. LOG_FILE=/opt/grocyscan/logs/app.log) "
                "and restart the service to persist logs."
            ),
            "log_file": None,
        }

    path = Path(settings.log_file)
    if not path.exists():
        buffered = [
            _strip_ansi(line.rstrip("\n\r"))
            for line in get_log_buffer_lines(MAX_LINES)
        ]
        return {
            "lines": buffered,
            "message": (
                f"Log file not found: {path}. Showing in-memory logs instead. "
                "Create the file or set LOG_FILE to a path the app can write to."
            ),
            "log_file": settings.log_file,
        }

    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except OSError as e:
        buffered = [
            _strip_ansi(line.rstrip("\n\r"))
            for line in get_log_buffer_lines(MAX_LINES)
        ]
        return {
            "lines": buffered,
            "message": f"Cannot read log file: {e}. Showing in-memory logs instead.",
            "log_file": settings.log_file,
        }

    # Last N lines: strip trailing newlines and ANSI codes for readable display
    trimmed = [
        _strip_ansi(line.rstrip("\n\r")) for line in lines[-MAX_LINES:]
    ]
    return {"lines": trimmed, "message": None, "log_file": settings.log_file}


@router.post("/clear")
async def clear_logs() -> dict:
    """Truncate the configured log file. Requires LOG_FILE to be set and writable."""
    if not settings.log_file or not settings.log_file.strip():
        clear_log_buffer()
        return {
            "message": "In-memory logs cleared. Set LOG_FILE to clear persisted logs.",
            "log_file": None,
        }
    path = Path(settings.log_file)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Log file not found: {path}")
    try:
        path.write_text("")
    except OSError as e:
        raise HTTPException(
            status_code=403,
            detail=f"Cannot write to log file: {e}",
        ) from e
    clear_log_buffer()
    return {"message": "Log file cleared.", "log_file": settings.log_file}


@router.post("/test")
async def write_test_log() -> dict:
    """Write a test log entry for the Logs UI."""
    logger.info("Logs UI test message")
    return {"message": "Test log entry written."}
