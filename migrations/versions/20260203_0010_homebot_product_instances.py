"""Homebot product_instances table (Phase 4 - LPN instance tracking).

Revision ID: 0010
Revises: 0009
Create Date: 2026-02-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create homebot.product_instances for LPN tracking."""
    op.create_table(
        "product_instances",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("lpn", sa.String(100), nullable=True),
        sa.Column("remaining_quantity", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("expiration_date", sa.Date(), nullable=True),
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
            ["tenant_id"], ["homebot.tenants.id"], name="fk_homebot_product_instances_tenant_id"
        ),
        sa.ForeignKeyConstraint(
            ["product_id"], ["homebot.products.id"], name="fk_homebot_product_instances_product_id"
        ),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["homebot.locations.id"],
            name="fk_homebot_product_instances_location_id",
        ),
        schema="homebot",
    )
    op.create_index(
        "ix_homebot_product_instances_tenant_product",
        "product_instances",
        ["tenant_id", "product_id"],
        schema="homebot",
    )
    op.create_index(
        "ix_homebot_product_instances_lpn",
        "product_instances",
        ["tenant_id", "lpn"],
        unique=True,
        schema="homebot",
    )

    op.execute("ALTER TABLE homebot.product_instances ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY homebot_product_instances_tenant_isolation ON homebot.product_instances
        FOR ALL USING (tenant_id::text = current_setting('app.tenant_id', true))
    """)


def downgrade() -> None:
    """Drop homebot.product_instances."""
    op.execute(
        "DROP POLICY IF EXISTS homebot_product_instances_tenant_isolation ON homebot.product_instances"
    )
    op.drop_table("product_instances", schema="homebot")
