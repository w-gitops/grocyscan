"""Barcode lookup API v2 (Phase 2): OpenFoodFacts and fallbacks."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps_v2 import get_current_user_v2
from app.services.lookup import lookup_manager

router = APIRouter()


@router.get("/barcode/{code}")
async def lookup_barcode(
    code: str,
    _user: str = Depends(get_current_user_v2),
) -> dict:
    """Look up product data by barcode. Returns 404 if not found."""
    if not code or not code.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Barcode required")
    result = await lookup_manager.lookup(code.strip(), skip_cache=False)
    if not result.found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown barcode")
    return {
        "barcode": result.barcode,
        "provider": result.provider,
        "name": result.name,
        "brand": result.brand,
        "description": result.description,
        "category": result.category,
        "image_url": result.image_url,
        "quantity": result.quantity,
        "quantity_unit": result.quantity_unit,
        "nutrition": result.nutrition,
        "ingredients": result.ingredients,
    }
