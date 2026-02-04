"""Stock API v2 (Phase 2): add, consume, transfer."""

import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_v2 import get_current_user_v2, get_db_homebot, get_tenant_id_v2
from app.db.homebot_models import HomebotStock, HomebotStockTransaction
from app.schemas.v2.stock import StockAddRequest, StockConsumeRequest, StockResponse, StockTransferRequest

router = APIRouter()


@router.post("/add", response_model=StockResponse)
async def add_stock(
    body: StockAddRequest,
    tenant_id: uuid.UUID = Depends(get_tenant_id_v2),
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> StockResponse:
    """Add quantity to stock. Creates stock row if needed for product+location."""
    r = await db.execute(
        select(HomebotStock).where(
            HomebotStock.tenant_id == tenant_id,
            HomebotStock.product_id == body.product_id,
            HomebotStock.location_id == body.location_id,
        )
    )
    row = r.scalar_one_or_none()
    if row:
        row.quantity += body.quantity
        if body.expiration_date is not None:
            row.expiration_date = body.expiration_date
        await db.flush()
        db.add(
            HomebotStockTransaction(
                tenant_id=tenant_id,
                stock_id=row.id,
                transaction_type="add",
                quantity=body.quantity,
                to_location_id=body.location_id,
            )
        )
    else:
        row = HomebotStock(
            tenant_id=tenant_id,
            product_id=body.product_id,
            location_id=body.location_id,
            quantity=body.quantity,
            expiration_date=body.expiration_date,
        )
        db.add(row)
        await db.flush()
        db.add(
            HomebotStockTransaction(
                tenant_id=tenant_id,
                stock_id=row.id,
                transaction_type="add",
                quantity=body.quantity,
                to_location_id=body.location_id,
            )
        )
    await db.commit()
    await db.refresh(row)
    return StockResponse.model_validate(row)


@router.post("/consume")
async def consume_stock(
    body: StockConsumeRequest,
    tenant_id: uuid.UUID = Depends(get_tenant_id_v2),
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> dict[str, str]:
    """Consume quantity. If location_id omitted, deduct from first available stock."""
    stmt = select(HomebotStock).where(
        HomebotStock.tenant_id == tenant_id,
        HomebotStock.product_id == body.product_id,
        HomebotStock.quantity > 0,
    )
    if body.location_id is not None:
        stmt = stmt.where(HomebotStock.location_id == body.location_id)
    r = await db.execute(stmt.order_by(HomebotStock.expiration_date.asc().nulls_last()))
    rows = list(r.scalars().all())
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No stock found for product")
    remaining = body.quantity
    for row in rows:
        if remaining <= 0:
            break
        take = min(remaining, row.quantity)
        row.quantity -= take
        remaining -= take
        db.add(
            HomebotStockTransaction(
                tenant_id=tenant_id,
                stock_id=row.id,
                transaction_type="consume",
                quantity=-take,
            )
        )
    if remaining > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient stock",
        )
    await db.commit()
    return {"status": "ok", "message": "Stock consumed"}


@router.post("/transfer")
async def transfer_stock(
    body: StockTransferRequest,
    tenant_id: uuid.UUID = Depends(get_tenant_id_v2),
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> dict[str, str]:
    """Transfer quantity between locations. Creates audit trail."""
    r = await db.execute(
        select(HomebotStock).where(
            HomebotStock.tenant_id == tenant_id,
            HomebotStock.product_id == body.product_id,
            HomebotStock.location_id == body.from_location_id,
        )
    )
    from_row = r.scalar_one_or_none()
    if not from_row or from_row.quantity < body.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient stock at source location",
        )
    from_row.quantity -= body.quantity
    r2 = await db.execute(
        select(HomebotStock).where(
            HomebotStock.tenant_id == tenant_id,
            HomebotStock.product_id == body.product_id,
            HomebotStock.location_id == body.to_location_id,
        )
    )
    to_row = r2.scalar_one_or_none()
    if to_row:
        to_row.quantity += body.quantity
        to_id = to_row.id
    else:
        to_row = HomebotStock(
            tenant_id=tenant_id,
            product_id=body.product_id,
            location_id=body.to_location_id,
            quantity=body.quantity,
        )
        db.add(to_row)
        await db.flush()
        to_id = to_row.id
    db.add(
        HomebotStockTransaction(
            tenant_id=tenant_id,
            stock_id=from_row.id,
            transaction_type="transfer",
            quantity=-body.quantity,
            from_location_id=body.from_location_id,
            to_location_id=body.to_location_id,
        )
    )
    await db.commit()
    return {"status": "ok", "message": "Stock transferred"}
