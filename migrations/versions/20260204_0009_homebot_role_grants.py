"""Ensure app_user has privileges on homebot tables.

Revision ID: 0012
Revises: 0011
Create Date: 2026-02-04
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Grant app_user privileges on homebot tables and defaults."""
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
                EXECUTE 'GRANT USAGE ON SCHEMA homebot TO app_user';
                EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA homebot TO app_user';
                EXECUTE 'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA homebot TO app_user';
                EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA homebot GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user';
                EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA homebot GRANT USAGE, SELECT ON SEQUENCES TO app_user';
            END IF;
        EXCEPTION
            WHEN insufficient_privilege THEN
                RAISE NOTICE 'Skipping grants for app_user (insufficient privilege).';
        END $$;
        """
    )


def downgrade() -> None:
    """No-op: keep grants in place to avoid breaking deployments."""
    pass
