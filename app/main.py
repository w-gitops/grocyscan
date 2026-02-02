"""GrocyScan FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.middleware.rate_limit import RateLimitMiddleware
from app.api.middleware.session import SessionMiddleware
from app.api.routes import api_router
from app.config import settings
from app.core.exceptions import AppException, AuthenticationError
from app.core.logging import configure_logging, get_logger
from app.core.metrics import metrics_endpoint
from app.core.telemetry import configure_telemetry, instrument_fastapi
from app.db.database import close_db, init_db
from app.services.cache import cache_service
from app.services.queue import job_queue, register_workers
from app.ui.app import configure_nicegui

# Configure logging first
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Handles startup and shutdown events.

    Args:
        app: FastAPI application instance

    Yields:
        None
    """
    # Startup
    logger.info(
        "Starting GrocyScan",
        version=settings.grocyscan_version,
        environment=settings.grocyscan_env,
    )

    # Configure telemetry
    configure_telemetry()

    # Initialize database
    if settings.is_development:
        await init_db()
        logger.info("Database initialized (development mode)")

    # Connect to Redis cache
    await cache_service.connect()

    # Register and start job queue workers
    register_workers()
    await job_queue.start_worker()

    yield

    # Stop job queue worker
    await job_queue.stop_worker()

    # Disconnect from Redis
    await cache_service.disconnect()

    # Shutdown
    logger.info("Shutting down GrocyScan")
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """
    app = FastAPI(
        title="GrocyScan",
        description="Barcode scanning app for Grocy inventory management",
        version=settings.grocyscan_version,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url=settings.openapi_url if settings.docs_enabled else None,
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.is_development else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add rate limiting middleware
    if settings.is_production:
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=settings.external_api_rate_limit,
        )

    # Add session middleware
    app.add_middleware(SessionMiddleware)

    # Include API routes
    app.include_router(api_router, prefix="/api")

    # Add metrics endpoint
    if settings.metrics_enabled:
        app.add_route("/metrics", metrics_endpoint)

    # Exception handlers
    @app.exception_handler(AuthenticationError)
    async def auth_exception_handler(
        request: Request, exc: AuthenticationError
    ) -> JSONResponse:
        """Handle authentication exceptions.

        Args:
            request: The incoming request
            exc: The exception that was raised

        Returns:
            JSONResponse: Error response with 401 status
        """
        logger.warning(
            "Authentication error",
            error=exc.error_code,
            message=exc.message,
        )
        return JSONResponse(
            status_code=401,
            content=exc.to_dict(),
        )

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        """Handle application exceptions.

        Args:
            request: The incoming request
            exc: The exception that was raised

        Returns:
            JSONResponse: Error response
        """
        logger.warning(
            "Application exception",
            error=exc.error_code,
            message=exc.message,
            details=exc.details,
        )
        return JSONResponse(
            status_code=400,
            content=exc.to_dict(),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions.

        Args:
            request: The incoming request
            exc: The exception that was raised

        Returns:
            JSONResponse: Error response
        """
        logger.exception("Unexpected error", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {"error": str(exc)} if settings.is_development else None,
            },
        )

    # Instrument with OpenTelemetry
    instrument_fastapi(app)

    # Configure NiceGUI
    configure_nicegui()

    # Integrate NiceGUI with FastAPI (storage_secret enables app.storage.user for e.g. recent scans)
    from nicegui import ui
    ui.run_with(
        app,
        title="GrocyScan",
        favicon="🛒",
        storage_secret=settings.grocyscan_secret_key.get_secret_value(),
    )

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.grocyscan_host,
        port=settings.grocyscan_port,
        reload=settings.is_development,
    )
