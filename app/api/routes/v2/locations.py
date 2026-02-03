"""Locations API v2 (Phase 2): CRUD and hierarchy."""

import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_v2 import get_current_user_v2, get_db_homebot, get_tenant_id_v2
from app.db.homebot_models import HomebotLocation, HomebotLocationClosure
from app.schemas.v2.location import LocationCreate, LocationResponse, LocationUpdate

router = APIRouter()


async def _rebuild_closure_for_new_location(db: AsyncSession, location_id: uuid.UUID, parent_id: uuid.UUID | None) -> None:
    """Insert closure rows for a new location: self (depth 0) and all ancestors -> self."""
    db.add(HomebotLocationClosure(ancestor_id=location_id, descendant_id=location_id, depth=0))
    if parent_id:
        result = await db.execute(
            select(HomebotLocationClosure.ancestor_id, HomebotLocationClosure.depth).where(
                HomebotLocationClosure.descendant_id == parent_id
            )
        )
        for ancestor_id, depth in result.all():
            db.add(
                HomebotLocationClosure(
                    ancestor_id=ancestor_id,
                    descendant_id=location_id,
                    depth=depth + 1,
                )
            )


@router.post("", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    body: LocationCreate,
    tenant_id: uuid.UUID = Depends(get_tenant_id_v2),
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> LocationResponse:
    """Create a location. If parent_id given, updates closure table."""
    if body.parent_id:
        r = await db.execute(
            select(HomebotLocation).where(HomebotLocation.id == body.parent_id, HomebotLocation.tenant_id == tenant_id)
        )
        if not r.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent location not found")
    loc = HomebotLocation(
        tenant_id=tenant_id,
        parent_id=body.parent_id,
        name=body.name,
        location_type=body.location_type,
        description=body.description,
        sort_order=body.sort_order,
        is_freezer=body.is_freezer,
    )
    db.add(loc)
    await db.flush()
    await _rebuild_closure_for_new_location(db, loc.id, body.parent_id)
    await db.commit()
    await db.refresh(loc)
    return LocationResponse.model_validate(loc)


@router.get("/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: UUID,
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> LocationResponse:
    """Get location by ID."""
    r = await db.execute(select(HomebotLocation).where(HomebotLocation.id == location_id))
    loc = r.scalar_one_or_none()
    if not loc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    return LocationResponse.model_validate(loc)


@router.get("/{location_id}/descendants", response_model=list[LocationResponse])
async def get_descendants(
    location_id: UUID,
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> list[LocationResponse]:
    """Get all descendants of a location (tree) via closure table."""
    r = await db.execute(
        select(HomebotLocation)
        .join(HomebotLocationClosure, HomebotLocationClosure.descendant_id == HomebotLocation.id)
        .where(
            HomebotLocationClosure.ancestor_id == location_id,
            HomebotLocationClosure.depth > 0,
        )
    )
    locs = r.scalars().unique().all()
    return [LocationResponse.model_validate(l) for l in locs]


@router.get("", response_model=list[LocationResponse])
async def list_locations(
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> list[LocationResponse]:
    """List all locations for the tenant."""
    r = await db.execute(select(HomebotLocation).order_by(HomebotLocation.sort_order, HomebotLocation.name))
    return [LocationResponse.model_validate(l) for l in r.scalars().all()]


@router.patch("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: UUID,
    body: LocationUpdate,
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> LocationResponse:
    """Update a location (partial)."""
    r = await db.execute(select(HomebotLocation).where(HomebotLocation.id == location_id))
    loc = r.scalar_one_or_none()
    if not loc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(loc, k, v)
    await db.commit()
    await db.refresh(loc)
    return LocationResponse.model_validate(loc)
