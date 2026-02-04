"""Products API v2 (Phase 2): CRUD and search."""

import re
import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_v2 import get_current_user_v2, get_db_homebot, get_tenant_id_v2
from app.db.homebot_models import HomebotBarcode, HomebotProduct
from app.schemas.v2.product import ProductCreate, ProductResponse, ProductUpdate

router = APIRouter()


def _normalize_name(name: str) -> str:
    """Lowercase and collapse whitespace for search."""
    return re.sub(r"\s+", " ", name.lower().strip()) if name else ""


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    body: ProductCreate,
    tenant_id: uuid.UUID = Depends(get_tenant_id_v2),
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> ProductResponse:
    """Create a product. Optionally link a barcode."""
    name_normalized = _normalize_name(body.name)
    product = HomebotProduct(
        tenant_id=tenant_id,
        name=body.name,
        name_normalized=name_normalized or None,
        description=body.description,
        category=body.category,
        quantity_unit=body.quantity_unit,
        min_stock_quantity=body.min_stock_quantity,
        attributes=body.attributes or {},
    )
    db.add(product)
    await db.flush()
    if body.barcode and body.barcode.strip():
        barcode_row = HomebotBarcode(
            tenant_id=tenant_id,
            product_id=product.id,
            barcode=body.barcode.strip(),
            is_primary=True,
        )
        db.add(barcode_row)
    await db.commit()
    await db.refresh(product)
    return ProductResponse.model_validate(product)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> ProductResponse:
    """Get product by ID."""
    result = await db.execute(select(HomebotProduct).where(HomebotProduct.id == product_id, HomebotProduct.deleted_at.is_(None)))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return ProductResponse.model_validate(product)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    body: ProductUpdate,
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> ProductResponse:
    """Update a product (partial)."""
    result = await db.execute(select(HomebotProduct).where(HomebotProduct.id == product_id, HomebotProduct.deleted_at.is_(None)))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    data = body.model_dump(exclude_unset=True)
    if "name" in data and data["name"]:
        data["name_normalized"] = _normalize_name(data["name"]) or None
    for key, value in data.items():
        setattr(product, key, value)
    await db.commit()
    await db.refresh(product)
    return ProductResponse.model_validate(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> None:
    """Soft-delete a product."""
    from datetime import datetime, timezone

    result = await db.execute(select(HomebotProduct).where(HomebotProduct.id == product_id, HomebotProduct.deleted_at.is_(None)))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    product.deleted_at = datetime.now(timezone.utc)
    await db.commit()


@router.get("", response_model=list[ProductResponse])
async def list_products(
    q: str | None = None,
    barcode: str | None = None,
    category: str | None = None,
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> list[ProductResponse]:
    """List/search products. Use ?q= for name search, ?barcode= for exact barcode match."""
    from sqlalchemy import or_

    stmt = select(HomebotProduct).where(HomebotProduct.deleted_at.is_(None))
    if barcode and barcode.strip():
        stmt = stmt.join(HomebotBarcode, HomebotBarcode.product_id == HomebotProduct.id).where(
            HomebotBarcode.barcode == barcode.strip()
        )
    if q and q.strip():
        pattern = f"%{q.strip().lower()}%"
        stmt = stmt.where(
            or_(
                HomebotProduct.name.ilike(pattern),
                HomebotProduct.name_normalized.ilike(pattern),
            )
        )
    if category and category.strip():
        stmt = stmt.where(HomebotProduct.category == category.strip())
    result = await db.execute(stmt)
    products = result.scalars().unique().all()
    return [ProductResponse.model_validate(p) for p in products]
