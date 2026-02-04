"""Homebot products and barcodes tables (Phase 2).

Revision ID: 0003
Revises: 0002
Create Date: 2026-02-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create homebot.products and homebot.barcodes with RLS."""
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("name_normalized", sa.String(500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(255), nullable=True),
        sa.Column("quantity_unit", sa.String(50), nullable=True),
        sa.Column("min_stock_quantity", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("image_path", sa.String(500), nullable=True),
        sa.Column("attributes", postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default=sa.text("'{}'")),
        sa.Column("enable_lpn_tracking", sa.Boolean(), nullable=False, server_default=sa.text("false")),
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
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["homebot.tenants.id"], name="fk_homebot_products_tenant_id"),
        schema="homebot",
    )
    op.create_index("ix_homebot_products_tenant_id", "products", ["tenant_id"], schema="homebot")
    op.create_index("ix_homebot_products_tenant_name", "products", ["tenant_id", "name_normalized"], schema="homebot")
    op.create_index("ix_homebot_products_tenant_category", "products", ["tenant_id", "category"], schema="homebot")

    op.create_table(
        "barcodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("barcode", sa.String(100), nullable=False),
        sa.Column("barcode_type", sa.String(20), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["homebot.tenants.id"], name="fk_homebot_barcodes_tenant_id"),
        sa.ForeignKeyConstraint(["product_id"], ["homebot.products.id"], name="fk_homebot_barcodes_product_id"),
        schema="homebot",
    )
    op.create_index("ix_homebot_barcodes_tenant_id", "barcodes", ["tenant_id"], schema="homebot")
    op.create_index("ix_homebot_barcodes_product_id", "barcodes", ["product_id"], schema="homebot")
    op.create_index(
        "ix_homebot_barcodes_tenant_barcode",
        "barcodes",
        ["tenant_id", "barcode"],
        unique=True,
        schema="homebot",
    )

    op.execute("ALTER TABLE homebot.products ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY homebot_products_tenant_isolation ON homebot.products
        FOR ALL USING (tenant_id::text = current_setting('app.tenant_id', true))
    """)
    op.execute("ALTER TABLE homebot.barcodes ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY homebot_barcodes_tenant_isolation ON homebot.barcodes
        FOR ALL USING (tenant_id::text = current_setting('app.tenant_id', true))
    """)


def downgrade() -> None:
    """Drop products and barcodes."""
    op.execute("DROP POLICY IF EXISTS homebot_barcodes_tenant_isolation ON homebot.barcodes")
    op.execute("DROP POLICY IF EXISTS homebot_products_tenant_isolation ON homebot.products")
    op.drop_table("barcodes", schema="homebot")
    op.drop_table("products", schema="homebot")
