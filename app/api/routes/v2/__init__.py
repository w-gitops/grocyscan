"""API v2 routes (Homebot Phase 1 + Phase 2)."""

from fastapi import APIRouter

from app.api.routes.v2 import auth as auth_v2
from app.api.routes.v2 import devices as devices_v2
from app.api.routes.v2 import health as health_v2
from app.api.routes.v2 import locations as locations_v2
from app.api.routes.v2 import lookup as lookup_v2
from app.api.routes.v2 import people as people_v2
from app.api.routes.v2 import products as products_v2
from app.api.routes.v2 import stock as stock_v2

v2_router = APIRouter()
v2_router.include_router(health_v2.router, tags=["health"])
v2_router.include_router(auth_v2.router, prefix="/auth", tags=["auth"])
v2_router.include_router(devices_v2.router, prefix="/devices", tags=["devices"])
v2_router.include_router(people_v2.router, prefix="/people", tags=["people"])
v2_router.include_router(products_v2.router, prefix="/products", tags=["products"])
v2_router.include_router(locations_v2.router, prefix="/locations", tags=["locations"])
v2_router.include_router(stock_v2.router, prefix="/stock", tags=["stock"])
v2_router.include_router(lookup_v2.router, prefix="/lookup", tags=["lookup"])
