"""Database migration status and upgrade (admin). Requires session auth."""

import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

router = APIRouter()


def _project_root() -> Path:
    """Project root (directory containing alembic.ini / migrations)."""
    # app/api/routes/migrations.py -> app -> api -> routes -> 3 parents = app/; one more = project root
    return Path(__file__).resolve().parent.parent.parent.parent


def _require_session(request: Request) -> None:
    """Raise if not authenticated (session)."""
    if not getattr(request.state, "user_id", None):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")


class MigrationStatusResponse(BaseModel):
    """Current migration revision."""

    current: str
    output: str


class MigrationUpgradeResponse(BaseModel):
    """Result of running migrations."""

    success: bool
    output: str
    error: str = ""


@router.get("/status", response_model=MigrationStatusResponse)
async def get_migration_status(request: Request) -> MigrationStatusResponse:
    """Return current Alembic revision (e.g. 0007). Requires login."""
    _require_session(request)
    root = _project_root()
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "current"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=15,
        )
        out = (result.stdout or "").strip()
        err = (result.stderr or "").strip()
        # alembic current prints revision to stdout; may be empty if no migrations run
        rev = out.splitlines()[0].strip() if out else "(none)"
        return MigrationStatusResponse(current=rev, output=out or err or "(no output)")
    except subprocess.TimeoutExpired:
        return MigrationStatusResponse(current="(timeout)", output="Command timed out")
    except Exception as e:
        return MigrationStatusResponse(current="(error)", output=str(e))


@router.post("/upgrade", response_model=MigrationUpgradeResponse)
async def run_migrations_upgrade(request: Request) -> MigrationUpgradeResponse:
    """Run alembic upgrade head. Requires login. Use only if you have admin access."""
    _require_session(request)
    root = _project_root()
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=120,
        )
        out = (result.stdout or "").strip()
        err = (result.stderr or "").strip()
        return MigrationUpgradeResponse(
            success=result.returncode == 0,
            output=out,
            error=err,
        )
    except subprocess.TimeoutExpired:
        return MigrationUpgradeResponse(
            success=False,
            output="",
            error="Command timed out (120s)",
        )
    except Exception as e:
        return MigrationUpgradeResponse(success=False, output="", error=str(e))
