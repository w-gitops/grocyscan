"""Labels API v2 (Phase 4): templates, preview, print."""

import uuid
from fastapi import APIRouter, Depends, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_v2 import get_current_user_v2, get_db_homebot, get_tenant_id_v2
from app.db.homebot_models import HomebotLabelTemplate
from app.schemas.v2.label import (
    LabelPreviewRequest,
    LabelPrintRequest,
    LabelTemplateCreate,
    LabelTemplateResponse,
)

router = APIRouter()


@router.post("", response_model=LabelTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_label_template(
    body: LabelTemplateCreate,
    tenant_id: uuid.UUID = Depends(get_tenant_id_v2),
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> LabelTemplateResponse:
    """Create label template."""
    row = HomebotLabelTemplate(
        tenant_id=tenant_id,
        name=body.name,
        template_type=body.template_type,
        schema=(body.schema_ if body.schema_ is not None else {}),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return LabelTemplateResponse.model_validate(row)


@router.post("/preview", response_class=Response)
async def preview_label(
    body: LabelPreviewRequest,
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> Response:
    """Return label as PNG image (placeholder: 200x100 PNG)."""
    # Placeholder: return minimal PNG (1x1 or small) for tests
    import base64
    # 1x1 transparent PNG
    png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    return Response(
        content=base64.b64decode(png_b64),
        media_type="image/png",
    )


@router.post("/print", status_code=status.HTTP_202_ACCEPTED)
async def print_label(
    body: LabelPrintRequest,
    tenant_id: uuid.UUID = Depends(get_tenant_id_v2),
    db: AsyncSession = Depends(get_db_homebot),
    _user: str = Depends(get_current_user_v2),
) -> dict:
    """Send label to printer (stub: accept and return job id). Printer URL per tenant TBD."""
    return {"job_id": str(uuid.uuid4()), "status": "queued"}
