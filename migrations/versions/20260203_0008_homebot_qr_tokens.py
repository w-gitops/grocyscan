"""Homebot qr_tokens table (Phase 4 - QR routing).

Revision ID: 0008
Revises: 0007
Create Date: 2026-02-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create homebot.qr_tokens for QR token system."""
    op.create_table(
        "qr_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("namespace", sa.String(50), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("checksum", sa.String(5), nullable=True),
        sa.Column("state", sa.String(20), nullable=False, server_default=sa.text("'unassigned'")),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["homebot.tenants.id"], name="fk_homebot_qr_tokens_tenant_id"),
        schema="homebot",
    )
    op.create_index(
        "ix_homebot_qr_tokens_tenant_namespace_code",
        "qr_tokens",
        ["tenant_id", "namespace", "code"],
        schema="homebot",
    )
    op.create_index(
        "ix_homebot_qr_tokens_namespace_code",
        "qr_tokens",
        ["namespace", "code"],
        unique=True,
        schema="homebot",
    )
    op.create_index("ix_homebot_qr_tokens_state", "qr_tokens", ["state"], schema="homebot")

    op.execute("ALTER TABLE homebot.qr_tokens ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY homebot_qr_tokens_tenant_isolation ON homebot.qr_tokens
        FOR ALL USING (tenant_id::text = current_setting('app.tenant_id', true))
    """)
    # Allow SELECT for public redirect lookup when app.allow_qr_lookup=1
    op.execute("""
        CREATE POLICY homebot_qr_tokens_public_lookup ON homebot.qr_tokens
        FOR SELECT USING (current_setting('app.allow_qr_lookup', true) = '1')
    """)


def downgrade() -> None:
    """Drop homebot.qr_tokens."""
    op.execute("DROP POLICY IF EXISTS homebot_qr_tokens_public_lookup ON homebot.qr_tokens")
    op.execute("DROP POLICY IF EXISTS homebot_qr_tokens_tenant_isolation ON homebot.qr_tokens")
    op.drop_table("qr_tokens", schema="homebot")
