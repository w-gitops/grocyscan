"""Homebot label_templates table (Phase 4 - label printing).

Revision ID: 0009
Revises: 0008
Create Date: 2026-02-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create homebot.label_templates."""
    op.create_table(
        "label_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("template_type", sa.String(50), nullable=False),
        sa.Column("schema", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["homebot.tenants.id"], name="fk_homebot_label_templates_tenant_id"
        ),
        schema="homebot",
    )
    op.create_index(
        "ix_homebot_label_templates_tenant_id", "label_templates", ["tenant_id"], schema="homebot"
    )

    op.execute("ALTER TABLE homebot.label_templates ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY homebot_label_templates_tenant_isolation ON homebot.label_templates
        FOR ALL USING (tenant_id::text = current_setting('app.tenant_id', true))
    """)


def downgrade() -> None:
    """Drop homebot.label_templates."""
    op.execute("DROP POLICY IF EXISTS homebot_label_templates_tenant_isolation ON homebot.label_templates")
    op.drop_table("label_templates", schema="homebot")
