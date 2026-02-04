"""GrocyScan FastAPI application entry point."""

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles


class SpaStaticFiles(StaticFiles):
    """StaticFiles that serves index.html for missing paths (SPA client-side routing)."""

    async def get_response(self, path: str, scope: dict):
        """Serve index.html when path is not a file (so /scan, /login etc. work on hard refresh)."""
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code == 404 and path.strip("/") and path != "index.html":
                return await super().get_response("index.html", scope)
            raise

from app.api.middleware.correlation_id import CorrelationIdMiddleware
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
        "Starting %s",
        settings.app_title,
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
    logger.info("Shutting down %s", settings.app_title)
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """
    app = FastAPI(
        title=settings.app_title,
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
    # Correlation ID (Phase 1: requests logged with correlation ID)
    app.add_middleware(CorrelationIdMiddleware)

    # Include API routes
    app.include_router(api_router, prefix="/api")

    # Root health (Phase 1: GET /health returns 200)
    @app.get("/health")
    async def root_health() -> dict[str, str]:
        return {"status": "healthy"}

    # PWA (Phase 3 [12]): manifest and service worker for installability
    _pwa_dir = Path(__file__).parent / "static" / "pwa"

    @app.get("/manifest.json", include_in_schema=False)
    async def pwa_manifest() -> JSONResponse:
        manifest_path = _pwa_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["name"] = settings.app_title
        manifest["short_name"] = settings.app_title
        return JSONResponse(
            manifest,
            media_type="application/manifest+json",
            headers={"Cache-Control": "public, max-age=300"},
        )

    @app.get("/sw.js", include_in_schema=False)
    async def pwa_service_worker() -> FileResponse:
        return FileResponse(
            _pwa_dir / "sw.js",
            media_type="application/javascript",
            headers={"Service-Worker-Allowed": "/"},
        )

    # Vue frontend at / when frontend/dist exists (NiceGUI disabled)
    _frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
    if _frontend_dist.exists():
        app.mount(
            "/",
            SpaStaticFiles(directory=_frontend_dist, html=True),
            name="vue-app",
        )

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
