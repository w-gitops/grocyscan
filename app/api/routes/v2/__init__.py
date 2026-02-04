"""API v2 routes (Homebot Phase 1 + Phase 2 + Phase 4)."""

from fastapi import APIRouter

from app.api.routes.v2 import auth as auth_v2
from app.api.routes.v2 import devices as devices_v2
from app.api.routes.v2 import health as health_v2
from app.api.routes.v2 import instances as instances_v2
from app.api.routes.v2 import labels as labels_v2
from app.api.routes.v2 import locations as locations_v2
from app.api.routes.v2 import lookup as lookup_v2
from app.api.routes.v2 import products as products_v2
from app.api.routes.v2 import qr_tokens as qr_tokens_v2
from app.api.routes.v2 import stock as stock_v2

v2_router = APIRouter()
v2_router.include_router(health_v2.router, tags=["health"])
v2_router.include_router(auth_v2.router, prefix="/auth", tags=["auth"])
v2_router.include_router(devices_v2.router, prefix="/devices", tags=["devices"])
v2_router.include_router(products_v2.router, prefix="/products", tags=["products"])
v2_router.include_router(locations_v2.router, prefix="/locations", tags=["locations"])
v2_router.include_router(stock_v2.router, prefix="/stock", tags=["stock"])
v2_router.include_router(lookup_v2.router, prefix="/lookup", tags=["lookup"])
v2_router.include_router(qr_tokens_v2.router, prefix="/qr-tokens", tags=["qr-tokens"])
v2_router.include_router(labels_v2.router, prefix="/labels", tags=["labels"])
v2_router.include_router(instances_v2.router, prefix="/instances", tags=["instances"])
