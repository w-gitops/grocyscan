"""Product instances (LPN) API v2 (Phase 4)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_v2 import get_current_user_v2, get_db_homebot, get_tenant_id_v2
from app.db.homebot_models import HomebotProductInstance
from app.schemas.v2.instance import (
    ProductInstanceConsume,
    ProductInstanceCreate,
    ProductInstanceResponse,
)

router = APIRouter()


@router.post("", response_model=ProductInstanceResponse, status_code=status.HTTP_201_CREATED)
async def create_instance(
    body: ProductInstanceCreate,
    tenant_id: uuid.UUID = Depends(get_tenant_id_v2),
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> ProductInstanceResponse:
    """Create product instance (LPN)."""
    row = HomebotProductInstance(
        tenant_id=tenant_id,
        product_id=body.product_id,
        location_id=body.location_id,
        lpn=body.lpn,
        remaining_quantity=body.remaining_quantity,
        expiration_date=body.expiration_date,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return ProductInstanceResponse.model_validate(row)


@router.get("/{instance_id:uuid}", response_model=ProductInstanceResponse)
async def get_instance(
    instance_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> ProductInstanceResponse:
    """Get product instance by id."""
    result = await db.execute(select(HomebotProductInstance).where(HomebotProductInstance.id == instance_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instance not found")
    return ProductInstanceResponse.model_validate(row)


@router.post("/{instance_id:uuid}/consume", response_model=ProductInstanceResponse)
async def consume_instance(
    instance_id: uuid.UUID,
    body: ProductInstanceConsume,
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> ProductInstanceResponse:
    """Consume quantity from instance (FIFO by expiration). Decrements remaining_quantity."""
    result = await db.execute(select(HomebotProductInstance).where(HomebotProductInstance.id == instance_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instance not found")
    if row.remaining_quantity < body.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Not enough quantity (has {row.remaining_quantity})",
        )
    row.remaining_quantity -= body.quantity
    await db.commit()
    await db.refresh(row)
    return ProductInstanceResponse.model_validate(row)
