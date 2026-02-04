"""Seed default tenant so /api/me device registration works when no tenant exists.

Revision ID: 0007
Revises: 0006
Create Date: 2026-02-03

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Fixed UUID for the default tenant (single-tenant / first-tenant use case)
DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    """Insert default tenant if none exists (idempotent)."""
    op.execute(
        f"""
        INSERT INTO homebot.tenants (id, name, slug, settings, created_at, updated_at)
        VALUES (
            '{DEFAULT_TENANT_ID}'::uuid,
            'Default',
            'default',
            NULL,
            now(),
            now()
        )
        ON CONFLICT (id) DO NOTHING
        """
    )


def downgrade() -> None:
    """Remove default tenant (only if it's our seeded one)."""
    op.execute(
        f"DELETE FROM homebot.tenants WHERE id = '{DEFAULT_TENANT_ID}'::uuid"
    )
