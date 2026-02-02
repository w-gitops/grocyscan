"""OpenTelemetry configuration for distributed tracing."""

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.config import settings


def configure_telemetry() -> None:
    """Configure OpenTelemetry tracing.

    Sets up the tracer provider, exporter, and auto-instrumentation
    for FastAPI, HTTPX, and SQLAlchemy.
    """
    if not settings.otel_enabled:
        return

    # Create resource with service information
    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
            "service.version": settings.grocyscan_version,
            "deployment.environment": settings.grocyscan_env,
        }
    )

    # Create tracer provider
    tracer_provider = TracerProvider(resource=resource)

    # Configure OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint=settings.otel_exporter_otlp_endpoint,
        insecure=settings.otel_exporter_otlp_insecure,
    )

    # Add span processor
    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Set the global tracer provider
    trace.set_tracer_provider(tracer_provider)


def instrument_fastapi(app: "FastAPI") -> None:  # noqa: F821
    """Instrument FastAPI application for tracing.

    Args:
        app: FastAPI application instance
    """
    if not settings.otel_enabled:
        return

    FastAPIInstrumentor.instrument_app(app)


def instrument_httpx() -> None:
    """Instrument HTTPX client for tracing."""
    if not settings.otel_enabled:
        return

    HTTPXClientInstrumentor().instrument()


def instrument_sqlalchemy(engine: "Engine") -> None:  # noqa: F821
    """Instrument SQLAlchemy for tracing.

    Args:
        engine: SQLAlchemy engine instance
    """
    if not settings.otel_enabled:
        return

    SQLAlchemyInstrumentor().instrument(engine=engine)


def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer instance.

    Args:
        name: Tracer name (usually __name__)

    Returns:
        A tracer instance
    """
    return trace.get_tracer(name)
