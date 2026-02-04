"""Structured logging configuration using structlog."""

import logging
import sys
from pathlib import Path
from typing import Any

import structlog
from opentelemetry import trace

from app.config import settings


def add_otel_context(
    logger: Any,  # noqa: ANN401
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Add OpenTelemetry trace context to every log event.

    Args:
        logger: The wrapped logger object
        method_name: The name of the log method called
        event_dict: The event dictionary containing log data

    Returns:
        Updated event dictionary with trace context
    """
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        ctx = span.get_span_context()
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
    return event_dict


def configure_logging() -> None:
    """Configure structured logging with OpenTelemetry context.

    Sets up structlog with appropriate processors for either JSON
    or console output based on settings.
    """
    # Shared processors for all output formats
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.ExtraAdder(),
    ]

    # Add OpenTelemetry context if enabled
    if settings.otel_enabled:
        shared_processors.append(add_otel_context)

    shared_processors.append(structlog.processors.StackInfoRenderer())

    # Configure output format
    if settings.log_format == "json":
        processors: list[structlog.types.Processor] = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    log_level = getattr(logging, settings.log_level)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    if settings.log_format == "json":
        # For JSON output, use a simple formatter (structlog handles formatting)
        console_handler.setFormatter(logging.Formatter("%(message)s"))
    else:
        # For console output, use a simple formatter
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )

    root_logger.addHandler(console_handler)

    # Add file handler if configured
    if settings.log_file and settings.log_file.strip():
        log_path = Path(settings.log_file.strip())
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setLevel(log_level)
            file_handler.setFormatter(logging.Formatter("%(message)s"))
            root_logger.addHandler(file_handler)
        except OSError:
            # Do not fail startup if log file cannot be created
            import warnings
            warnings.warn(
                f"Cannot create log file {log_path}. In-app log viewer will be empty.",
                UserWarning,
                stacklevel=2,
            )

    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structlog logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        A bound structlog logger
    """
    return structlog.get_logger(name)
