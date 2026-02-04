"""QR tokens API v2 (Phase 4)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_v2 import get_current_user_v2, get_db_homebot, get_tenant_id_v2
from app.db.homebot_models import HomebotQrToken
from app.schemas.v2.qr import QrTokenAssign, QrTokenCreate, QrTokenResponse
from app.services.qr import generate_token, validate_checksum

router = APIRouter()


def _parse_token(token: str) -> tuple[str, str, str] | None:
    """Parse NS-CODE-CHECK or CODE-CHECK. Returns (namespace, code, check) or None."""
    token = token.strip().upper()
    if "-" in token:
        parts = token.split("-")
        if len(parts) == 3:
            return parts[0], parts[1], parts[2]
        if len(parts) == 2:
            return "", parts[0], parts[1]
    if len(token) >= 2:
        return "", token[:-1], token[-1]
    return None


@router.post("", response_model=QrTokenResponse, status_code=status.HTTP_201_CREATED)
async def create_qr_token(
    body: QrTokenCreate,
    tenant_id: uuid.UUID = Depends(get_tenant_id_v2),
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> QrTokenResponse:
    """Create a new QR token (generate code with Crockford Base32 + checksum)."""
    full_token = generate_token(body.namespace)
    parsed = _parse_token(full_token)
    if not parsed:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Token generation failed")
    namespace, code, check = parsed
    ns = namespace or body.namespace.upper()
    row = HomebotQrToken(
        tenant_id=tenant_id,
        namespace=ns,
        code=code,
        checksum=check,
        state="unassigned",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return QrTokenResponse.model_validate(row)


@router.post("/{token_id:uuid}/assign", response_model=QrTokenResponse)
async def assign_qr_token(
    token_id: uuid.UUID,
    body: QrTokenAssign,
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> QrTokenResponse:
    """Assign token to product/location/instance. Re-assignment revokes old."""
    result = await db.execute(select(HomebotQrToken).where(HomebotQrToken.id == token_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR token not found")
    row.state = "assigned"
    row.entity_type = body.entity_type
    row.entity_id = body.entity_id
    await db.commit()
    await db.refresh(row)
    return QrTokenResponse.model_validate(row)


@router.get("/by-token/{token_str:path}", response_model=QrTokenResponse)
async def get_qr_token_by_token(
    token_str: str,
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> QrTokenResponse:
    """Get QR token by full token string (NS-CODE-CHECK)."""
    if not validate_checksum(token_str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token checksum")
    parsed = _parse_token(token_str)
    if not parsed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token format")
    namespace, code, _ = parsed
    ns = namespace or ""
    result = await db.execute(
        select(HomebotQrToken).where(
            HomebotQrToken.namespace == ns,
            HomebotQrToken.code == code,
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR token not found")
    return QrTokenResponse.model_validate(row)
