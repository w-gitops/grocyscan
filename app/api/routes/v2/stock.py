"""Stock API v2 (Phase 2+): list, add, consume, transfer, inventory, open, edit, undo."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_v2 import get_current_user_v2, get_db_homebot, get_tenant_id_v2
from app.db.homebot_models import HomebotLocation, HomebotProduct, HomebotStock, HomebotStockTransaction
from app.schemas.v2.stock import (
    StockAddRequest,
    StockConsumeRequest,
    StockEntryEditRequest,
    StockEntryResponse,
    StockInventoryRequest,
    StockOpenRequest,
    StockResponse,
    StockTransactionResponse,
    StockTransferRequest,
)

router = APIRouter()


@router.get("", response_model=list[StockEntryResponse])
async def list_stock(
    product_id: UUID | None = Query(None, description="Filter by product"),
    location_id: UUID | None = Query(None, description="Filter by location"),
    tenant_id: uuid.UUID = Depends(get_tenant_id_v2),
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> list[StockEntryResponse]:
    """List stock entries (inventory overview). Optionally filter by product_id or location_id."""
    stmt = (
        select(HomebotStock, HomebotProduct.name, HomebotLocation.name)
        .join(HomebotProduct, HomebotStock.product_id == HomebotProduct.id)
        .outerjoin(HomebotLocation, HomebotStock.location_id == HomebotLocation.id)
        .where(HomebotProduct.deleted_at.is_(None))
    )
    if product_id is not None:
        stmt = stmt.where(HomebotStock.product_id == product_id)
    if location_id is not None:
        stmt = stmt.where(HomebotStock.location_id == location_id)
    stmt = stmt.order_by(HomebotProduct.name, HomebotLocation.name.asc().nulls_last())
    result = await db.execute(stmt)
    rows = result.all()
    return [
        StockEntryResponse(
            id=row[0].id,
            product_id=row[0].product_id,
            product_name=row[1],
            location_id=row[0].location_id,
            location_name=row[2],
            quantity=row[0].quantity,
            expiration_date=row[0].expiration_date,
            created_at=row[0].created_at,
            updated_at=row[0].updated_at,
            stock_id=row[0].stock_id,
            purchased_date=row[0].purchased_date,
            price=row[0].price,
            open=row[0].open,
            opened_date=row[0].opened_date,
            note=row[0].note,
        )
        for row in rows
    ]


def _generate_stock_id() -> str:
    """Generate a unique stock_id for Grocycode tracking."""
    return str(uuid.uuid4())


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
        if body.price is not None:
            row.price = body.price
        if body.purchased_date is not None:
            row.purchased_date = body.purchased_date
        if body.note is not None:
            row.note = body.note
        await db.flush()
        db.add(
            HomebotStockTransaction(
                tenant_id=tenant_id,
                stock_id=row.id,
                product_id=body.product_id,
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
            stock_id=_generate_stock_id(),
            price=body.price,
            purchased_date=body.purchased_date,
            note=body.note,
        )
        db.add(row)
        await db.flush()
        db.add(
            HomebotStockTransaction(
                tenant_id=tenant_id,
                stock_id=row.id,
                product_id=body.product_id,
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
                product_id=body.product_id,
                transaction_type="consume",
                quantity=-take,
                spoiled=body.spoiled,
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
    """Transfer quantity between locations. Creates audit trail with correlation_id."""
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
    else:
        to_row = HomebotStock(
            tenant_id=tenant_id,
            product_id=body.product_id,
            location_id=body.to_location_id,
            quantity=body.quantity,
            stock_id=_generate_stock_id(),
        )
        db.add(to_row)
        await db.flush()

    # Create correlated transaction pair
    correlation_id = uuid.uuid4()
    db.add(
        HomebotStockTransaction(
            tenant_id=tenant_id,
            stock_id=from_row.id,
            product_id=body.product_id,
            transaction_type="transfer_from",
            quantity=-body.quantity,
            from_location_id=body.from_location_id,
            to_location_id=body.to_location_id,
            correlation_id=correlation_id,
        )
    )
    db.add(
        HomebotStockTransaction(
            tenant_id=tenant_id,
            stock_id=to_row.id,
            product_id=body.product_id,
            transaction_type="transfer_to",
            quantity=body.quantity,
            from_location_id=body.from_location_id,
            to_location_id=body.to_location_id,
            correlation_id=correlation_id,
        )
    )
    await db.commit()
    return {"status": "ok", "message": "Stock transferred"}


@router.post("/inventory", response_model=StockResponse)
async def inventory_stock(
    body: StockInventoryRequest,
    tenant_id: uuid.UUID = Depends(get_tenant_id_v2),
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> StockResponse:
    """Set stock to specific amount (inventory correction)."""
    r = await db.execute(
        select(HomebotStock).where(
            HomebotStock.tenant_id == tenant_id,
            HomebotStock.product_id == body.product_id,
            HomebotStock.location_id == body.location_id,
        )
    )
    row = r.scalar_one_or_none()
    if row:
        current = row.quantity
        diff = body.new_amount - current
        row.quantity = body.new_amount
        if body.best_before_date is not None:
            row.expiration_date = body.best_before_date
        await db.flush()
        db.add(
            HomebotStockTransaction(
                tenant_id=tenant_id,
                stock_id=row.id,
                product_id=body.product_id,
                transaction_type="inventory-correction",
                quantity=diff,
                to_location_id=body.location_id,
            )
        )
    else:
        if body.new_amount <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot set non-existing stock to zero or negative")
        row = HomebotStock(
            tenant_id=tenant_id,
            product_id=body.product_id,
            location_id=body.location_id,
            quantity=body.new_amount,
            expiration_date=body.best_before_date,
            stock_id=_generate_stock_id(),
        )
        db.add(row)
        await db.flush()
        db.add(
            HomebotStockTransaction(
                tenant_id=tenant_id,
                stock_id=row.id,
                product_id=body.product_id,
                transaction_type="inventory-correction",
                quantity=body.new_amount,
                to_location_id=body.location_id,
            )
        )
    await db.commit()
    await db.refresh(row)
    return StockResponse.model_validate(row)


@router.post("/open", response_model=StockResponse)
async def open_stock(
    body: StockOpenRequest,
    tenant_id: uuid.UUID = Depends(get_tenant_id_v2),
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> StockResponse:
    """Mark stock entry as opened. Recalculates best_before if product has after_open setting."""
    r = await db.execute(
        select(HomebotStock).where(
            HomebotStock.id == body.stock_entry_id,
            HomebotStock.tenant_id == tenant_id,
        )
    )
    row = r.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock entry not found")
    if row.open:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stock entry already opened")

    # Get product for after-open settings
    pr = await db.execute(select(HomebotProduct).where(HomebotProduct.id == row.product_id))
    product = pr.scalar_one_or_none()

    row.open = True
    row.opened_date = date.today()

    # Recalculate best_before if product has after_open setting
    if product and product.default_best_before_days_after_open:
        from datetime import timedelta
        row.expiration_date = date.today() + timedelta(days=product.default_best_before_days_after_open)

    # Handle move_on_open
    if product and product.move_on_open and product.default_consume_location_id:
        old_location_id = row.location_id
        row.location_id = product.default_consume_location_id
        correlation_id = uuid.uuid4()
        db.add(
            HomebotStockTransaction(
                tenant_id=tenant_id,
                stock_id=row.id,
                product_id=row.product_id,
                transaction_type="transfer_from",
                quantity=0,
                from_location_id=old_location_id,
                to_location_id=product.default_consume_location_id,
                correlation_id=correlation_id,
                notes="Auto-transfer on open",
            )
        )

    db.add(
        HomebotStockTransaction(
            tenant_id=tenant_id,
            stock_id=row.id,
            product_id=row.product_id,
            transaction_type="product-opened",
            quantity=0,
        )
    )
    await db.commit()
    await db.refresh(row)
    return StockResponse.model_validate(row)


@router.patch("/entries/{entry_id}", response_model=StockResponse)
async def edit_stock_entry(
    entry_id: UUID,
    body: StockEntryEditRequest,
    tenant_id: uuid.UUID = Depends(get_tenant_id_v2),
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> StockResponse:
    """Edit stock entry. Creates edit transaction pair for audit."""
    r = await db.execute(
        select(HomebotStock).where(
            HomebotStock.id == entry_id,
            HomebotStock.tenant_id == tenant_id,
        )
    )
    row = r.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock entry not found")

    correlation_id = uuid.uuid4()
    old_values = {
        "amount": row.quantity,
        "best_before_date": row.expiration_date,
        "location_id": row.location_id,
        "price": row.price,
        "note": row.note,
        "open": row.open,
    }

    # Apply updates
    if body.amount is not None:
        row.quantity = body.amount
    if body.best_before_date is not None:
        row.expiration_date = body.best_before_date
    if body.location_id is not None:
        row.location_id = body.location_id
    if body.price is not None:
        row.price = body.price
    if body.note is not None:
        row.note = body.note
    if body.open is not None:
        row.open = body.open
        if body.open and not row.opened_date:
            row.opened_date = date.today()

    # Create edit transaction pair
    db.add(
        HomebotStockTransaction(
            tenant_id=tenant_id,
            stock_id=row.id,
            product_id=row.product_id,
            transaction_type="stock-edit-old",
            quantity=0,
            correlation_id=correlation_id,
            notes=str(old_values),
        )
    )
    db.add(
        HomebotStockTransaction(
            tenant_id=tenant_id,
            stock_id=row.id,
            product_id=row.product_id,
            transaction_type="stock-edit-new",
            quantity=0,
            correlation_id=correlation_id,
            notes=str(body.model_dump(exclude_unset=True)),
        )
    )

    await db.commit()
    await db.refresh(row)
    return StockResponse.model_validate(row)


@router.post("/undo/{transaction_id}")
async def undo_transaction(
    transaction_id: UUID,
    tenant_id: uuid.UUID = Depends(get_tenant_id_v2),
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> dict[str, str]:
    """Undo a stock transaction. For transfers, undoes both legs via correlation_id."""
    r = await db.execute(
        select(HomebotStockTransaction).where(
            HomebotStockTransaction.id == transaction_id,
            HomebotStockTransaction.tenant_id == tenant_id,
        )
    )
    tx = r.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    if tx.undone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transaction already undone")

    # Get all related transactions via correlation_id
    transactions = [tx]
    if tx.correlation_id:
        cr = await db.execute(
            select(HomebotStockTransaction).where(
                HomebotStockTransaction.correlation_id == tx.correlation_id,
                HomebotStockTransaction.tenant_id == tenant_id,
            )
        )
        transactions = list(cr.scalars().all())

    for t in transactions:
        if t.undone:
            continue

        # Reverse the effect on stock
        if t.stock_id and t.quantity != 0:
            sr = await db.execute(select(HomebotStock).where(HomebotStock.id == t.stock_id))
            stock = sr.scalar_one_or_none()
            if stock:
                stock.quantity -= t.quantity  # Reverse the quantity change

        # Mark as undone
        t.undone = True
        t.undone_timestamp = datetime.now(timezone.utc)

    await db.commit()
    return {"status": "ok", "message": f"Undone {len(transactions)} transaction(s)"}


@router.get("/transactions", response_model=list[StockTransactionResponse])
async def list_transactions(
    product_id: UUID | None = Query(None, description="Filter by product"),
    limit: int = Query(100, le=500),
    tenant_id: uuid.UUID = Depends(get_tenant_id_v2),
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> list[StockTransactionResponse]:
    """List stock transactions (audit log)."""
    stmt = select(HomebotStockTransaction).order_by(HomebotStockTransaction.created_at.desc()).limit(limit)
    if product_id:
        stmt = stmt.where(HomebotStockTransaction.product_id == product_id)
    result = await db.execute(stmt)
    return [StockTransactionResponse.model_validate(t) for t in result.scalars().all()]
