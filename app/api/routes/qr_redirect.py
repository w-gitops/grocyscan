"""QR redirect: GET /q/{token} resolves token and redirects (Phase 4). No auth."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.homebot_models import HomebotQrToken
from app.services.qr import validate_checksum

router = APIRouter()


def _parse_token(token: str) -> tuple[str, str] | None:
    """Parse NS-CODE-CHECK or CODE-CHECK. Returns (namespace, code) or None."""
    token = token.strip().upper()
    if "-" in token:
        parts = token.split("-")
        if len(parts) == 3:
            return parts[0], parts[1]
        if len(parts) == 2:
            return "", parts[0]
    if len(token) >= 2:
        return "", token[:-1]
    return None


@router.get("/q/{token_str:path}")
async def qr_redirect(
    request: Request,
    token_str: str,
    db: AsyncSession = Depends(get_db),
):
    """Resolve QR token and redirect. Unassigned -> assignment UI; assigned -> entity detail."""
    if not validate_checksum(token_str):
        return RedirectResponse(url="/#/q/invalid", status_code=302)
    parsed = _parse_token(token_str)
    if not parsed:
        return RedirectResponse(url="/#/q/invalid", status_code=302)
    namespace, code = parsed
    await db.execute(text("SET LOCAL app.allow_qr_lookup = '1'"))
    result = await db.execute(
        select(HomebotQrToken).where(
            HomebotQrToken.namespace == (namespace or ""),
            HomebotQrToken.code == code,
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        return RedirectResponse(url="/#/q/not-found", status_code=302)
    if row.state == "unassigned":
        return RedirectResponse(url=f"/#/q/assign?token={token_str}", status_code=302)
    # Assigned: redirect to entity view (e.g. product or location)
    entity_type = row.entity_type or "product"
    entity_id = str(row.entity_id) if row.entity_id else ""
    return RedirectResponse(
        url=f"/#/q/{entity_type}/{entity_id}?token={token_str}",
        status_code=302,
    )
