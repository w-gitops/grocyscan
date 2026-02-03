"""Location management endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_locations() -> dict[str, str]:
    """List all locations.

    Returns:
        dict: List of locations
    """
    # TODO: Implement location listing
    return {"status": "not_implemented"}


@router.post("")
async def create_location() -> dict[str, str]:
    """Create a new location.

    Returns:
        dict: Created location info
    """
    # TODO: Implement location creation
    return {"status": "not_implemented"}


@router.get("/{code}")
async def get_location(code: str) -> dict[str, str]:
    """Get location by code.

    Args:
        code: The location code

    Returns:
        dict: Location details
    """
    # TODO: Implement get location
    return {"status": "not_implemented", "code": code}
