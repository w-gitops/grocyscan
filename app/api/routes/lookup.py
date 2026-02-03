"""Lookup endpoints (barcode-style search by product name)."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.lookup import lookup_manager

router = APIRouter()


class LookupSearchRequest(BaseModel):
    """Request to search products by name via external providers."""

    query: str = Field(..., min_length=2, max_length=200)
    limit: int = Field(20, ge=1, le=50)


class LookupSearchResultItem(BaseModel):
    """Single result from lookup search (internet providers)."""

    id: str
    name: str
    category: str | None = None
    image_url: str | None = None
    source: str
    barcode: str | None = None
    nutrition: dict | None = None
    description: str | None = None


class LookupSearchResponse(BaseModel):
    """Response from lookup search by name."""

    results: list[LookupSearchResultItem]
    total: int
    query: str


@router.post("/search-by-name", response_model=LookupSearchResponse)
async def search_by_name(request: LookupSearchRequest) -> LookupSearchResponse:
    """Search for products by name using external providers (OpenFoodFacts, Brave).

    Like a barcode scan lookup but triggered by a product name query.
    Returns results from OpenFoodFacts and Brave Search for the user to pick.
    """
    results = await lookup_manager.search_by_name(
        query=request.query,
        limit=request.limit,
    )
    items: list[LookupSearchResultItem] = []
    for i, r in enumerate(results):
        if not r.found or not r.name:
            continue
        items.append(
            LookupSearchResultItem(
                id=f"{r.provider}-{i}-{hash(r.name) % 10**8}",
                name=r.name,
                category=r.category,
                image_url=r.image_url,
                source=r.provider,
                barcode=r.barcode or None,
                nutrition=r.nutrition,
                description=r.description,
            )
        )
    return LookupSearchResponse(
        results=items[: request.limit],
        total=len(items),
        query=request.query,
    )
