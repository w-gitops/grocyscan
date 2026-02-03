"""Pydantic schemas for API v2."""

from app.schemas.v2.device import DeviceCreate, DeviceResponse, DeviceUpdatePreferences
from app.schemas.v2.location import LocationCreate, LocationResponse, LocationUpdate
from app.schemas.v2.product import ProductCreate, ProductResponse, ProductUpdate
from app.schemas.v2.stock import StockAddRequest, StockConsumeRequest, StockResponse, StockTransferRequest

__all__ = [
    "DeviceCreate",
    "DeviceResponse",
    "DeviceUpdatePreferences",
    "LocationCreate",
    "LocationResponse",
    "LocationUpdate",
    "ProductCreate",
    "ProductResponse",
    "ProductUpdate",
    "StockAddRequest",
    "StockConsumeRequest",
    "StockResponse",
    "StockTransferRequest",
]
