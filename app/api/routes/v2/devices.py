"""Devices API v2 (Phase 3): registration and preferences."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_v2 import get_current_user_v2, get_db_homebot, get_device_fingerprint, get_tenant_id_v2
from app.db.homebot_models import HomebotDevice
from app.schemas.v2.device import DeviceCreate, DeviceResponse, DeviceUpdatePreferences

router = APIRouter()


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def register_device(
    body: DeviceCreate,
    tenant_id: uuid.UUID = Depends(get_tenant_id_v2),
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> DeviceResponse:
    """Register a device (or update last_seen if already registered)."""
    result = await db.execute(
        select(HomebotDevice).where(
            HomebotDevice.tenant_id == tenant_id,
            HomebotDevice.fingerprint == body.fingerprint,
        )
    )
    device = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if device:
        device.name = body.name
        device.device_type = body.device_type
        device.last_seen_at = now
        await db.commit()
        await db.refresh(device)
        return DeviceResponse.model_validate(device)
    device = HomebotDevice(
        tenant_id=tenant_id,
        name=body.name,
        fingerprint=body.fingerprint,
        device_type=body.device_type,
        last_seen_at=now,
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return DeviceResponse.model_validate(device)


@router.get("/me", response_model=DeviceResponse)
async def get_my_device(
    fingerprint: str = Depends(get_device_fingerprint),
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> DeviceResponse:
    """Get current device by X-Device-ID (fingerprint)."""
    result = await db.execute(
        select(HomebotDevice).where(HomebotDevice.fingerprint == fingerprint)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not registered")
    return DeviceResponse.model_validate(device)


@router.patch("/me", response_model=DeviceResponse)
async def update_my_device_preferences(
    body: DeviceUpdatePreferences,
    fingerprint: str = Depends(get_device_fingerprint),
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> DeviceResponse:
    """Update device preferences (default location, action mode, etc.)."""
    result = await db.execute(
        select(HomebotDevice).where(HomebotDevice.fingerprint == fingerprint)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not registered")
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(device, key, value)
    await db.commit()
    await db.refresh(device)
    return DeviceResponse.model_validate(device)
