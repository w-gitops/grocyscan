"""API route modules."""

from fastapi import APIRouter

from app.api.routes import auth, health, jobs, locations, logs, lookup, products, scan, settings
from app.api.routes.v2 import v2_router

api_router = APIRouter()

# Include all route modules
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(v2_router, prefix="/v2")
api_router.include_router(scan.router, prefix="/scan", tags=["scan"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(lookup.router, prefix="/lookup", tags=["lookup"])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
