"""Product management endpoints."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import CurrentUserId, DbSession
from app.db.models import Product
from app.services.grocy import grocy_client

router = APIRouter()


class ProductSearchRequest(BaseModel):
    """Search parameters for products."""

    query: str = Field(..., min_length=2, max_length=200)
    include_grocy: bool = True
    limit: int = Field(20, ge=1, le=100)


class ProductSearchResult(BaseModel):
    """Single product search result."""

    id: str
    name: str
    category: str | None = None
    image_url: str | None = None
    source: str
    grocy_product_id: int | None = None


class ProductSearchResponse(BaseModel):
    """Search response with results."""

    results: list[ProductSearchResult]
    total: int
    query: str


@router.post("/search", response_model=ProductSearchResponse)
async def search_products(
    request: ProductSearchRequest,
    db: DbSession,
    user_id: CurrentUserId,
) -> ProductSearchResponse:
    """Search products by name.

    Searches both local database and Grocy API, merging and deduplicating results.
    """
    results: list[ProductSearchResult] = []
    query_lower = request.query.lower().strip()

    # Resolve user_id to UUID if it's the default string
    try:
        user_uuid = uuid.UUID(user_id) if user_id else None
    except (ValueError, TypeError):
        user_uuid = None

    # Search local database (if we have a valid user_id)
    if user_uuid:
        stmt = (
            select(Product)
            .where(Product.user_id == user_uuid)
            .where(Product.name_normalized.ilike(f"%{query_lower}%"))
            .limit(request.limit)
        )
        cursor = await db.execute(stmt)
        for product in cursor.scalars().all():
            results.append(
                ProductSearchResult(
                    id=str(product.id),
                    name=product.name,
                    category=product.category,
                    image_url=product.image_path,
                    source="local",
                    grocy_product_id=product.grocy_product_id,
                )
            )

    # Search Grocy products
    if request.include_grocy:
        try:
            grocy_products = await grocy_client.get_products()
            seen_grocy_ids = {r.grocy_product_id for r in results if r.grocy_product_id}
            for gp in grocy_products:
                if gp is None or not isinstance(gp, dict):
                    continue
                name = gp.get("name") or ""
                if query_lower not in name.lower():
                    continue
                gid = gp.get("id")
                if gid in seen_grocy_ids:
                    continue
                seen_grocy_ids.add(gid)
                results.append(
                    ProductSearchResult(
                        id=f"grocy-{gid}",
                        name=name,
                        category=None,  # Grocy returns product_group_id; could resolve to name
                        image_url=None,
                        source="grocy",
                        grocy_product_id=gid,
                    )
                )
        except Exception:
            pass

    # Sort: exact match first, then by name
    results.sort(key=lambda r: (0 if r.name.lower() == query_lower else 1, r.name.lower()))
    results = results[: request.limit]

    return ProductSearchResponse(
        results=results,
        total=len(results),
        query=request.query,
    )


@router.get("")
async def list_products() -> dict[str, str]:
    """List all products.

    Returns:
        dict: List of products
    """
    # TODO: Implement product listing
    return {"status": "not_implemented"}


@router.post("")
async def create_product() -> dict[str, str]:
    """Create a new product.

    Returns:
        dict: Created product info
    """
    # TODO: Implement product creation
    return {"status": "not_implemented"}


@router.get("/{product_id}")
async def get_product(product_id: str) -> dict[str, str]:
    """Get product by ID.

    Args:
        product_id: The product ID

    Returns:
        dict: Product details
    """
    # TODO: Implement get product
    return {"status": "not_implemented", "product_id": product_id}


@router.put("/{product_id}")
async def update_product(product_id: str) -> dict[str, str]:
    """Update a product.

    Args:
        product_id: The product ID

    Returns:
        dict: Updated product info
    """
    # TODO: Implement product update
    return {"status": "not_implemented", "product_id": product_id}


@router.delete("/{product_id}")
async def delete_product(product_id: str) -> dict[str, str]:
    """Delete a product.

    Args:
        product_id: The product ID

    Returns:
        dict: Deletion confirmation
    """
    # TODO: Implement product deletion
    return {"status": "not_implemented", "product_id": product_id}
