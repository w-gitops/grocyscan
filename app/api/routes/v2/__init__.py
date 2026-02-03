"""API v2 routes (Homebot Phase 1)."""

from fastapi import APIRouter

from app.api.routes.v2 import auth as auth_v2
from app.api.routes.v2 import health as health_v2

v2_router = APIRouter()
v2_router.include_router(health_v2.router, tags=["health"])
v2_router.include_router(auth_v2.router, prefix="/auth", tags=["auth"])
