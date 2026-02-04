"""Homebot stock and stock_transactions (Phase 2).

Revision ID: 0005
Revises: 0004
Create Date: 2026-02-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create homebot.stock and homebot.stock_transactions."""
    op.create_table(
        "stock",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default=sa.text("0")),
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
        sa.ForeignKeyConstraint(["tenant_id"], ["homebot.tenants.id"], name="fk_homebot_stock_tenant_id"),
        sa.ForeignKeyConstraint(["product_id"], ["homebot.products.id"], name="fk_homebot_stock_product_id"),
        sa.ForeignKeyConstraint(["location_id"], ["homebot.locations.id"], name="fk_homebot_stock_location_id"),
        schema="homebot",
    )
    op.create_index("ix_homebot_stock_tenant_id", "stock", ["tenant_id"], schema="homebot")
    op.create_index("ix_homebot_stock_product_id", "stock", ["product_id"], schema="homebot")
    op.create_index("ix_homebot_stock_location_id", "stock", ["location_id"], schema="homebot")
    op.create_index("ix_homebot_stock_expiration_date", "stock", ["expiration_date"], schema="homebot")

    op.create_table(
        "stock_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stock_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("transaction_type", sa.String(20), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("from_location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("to_location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["homebot.tenants.id"], name="fk_homebot_stock_tx_tenant_id"),
        sa.ForeignKeyConstraint(["stock_id"], ["homebot.stock.id"], name="fk_homebot_stock_tx_stock_id"),
        sa.ForeignKeyConstraint(
            ["from_location_id"],
            ["homebot.locations.id"],
            name="fk_homebot_stock_tx_from_location",
        ),
        sa.ForeignKeyConstraint(
            ["to_location_id"],
            ["homebot.locations.id"],
            name="fk_homebot_stock_tx_to_location",
        ),
        schema="homebot",
    )
    op.create_index("ix_homebot_stock_transactions_tenant_id", "stock_transactions", ["tenant_id"], schema="homebot")
    op.create_index("ix_homebot_stock_transactions_stock_id", "stock_transactions", ["stock_id"], schema="homebot")

    op.execute("ALTER TABLE homebot.stock ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY homebot_stock_tenant_isolation ON homebot.stock
        FOR ALL USING (tenant_id::text = current_setting('app.tenant_id', true))
    """)
    op.execute("ALTER TABLE homebot.stock_transactions ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY homebot_stock_transactions_tenant_isolation ON homebot.stock_transactions
        FOR ALL USING (tenant_id::text = current_setting('app.tenant_id', true))
    """)


def downgrade() -> None:
    """Drop stock and stock_transactions."""
    op.execute("DROP POLICY IF EXISTS homebot_stock_transactions_tenant_isolation ON homebot.stock_transactions")
    op.execute("DROP POLICY IF EXISTS homebot_stock_tenant_isolation ON homebot.stock")
    op.drop_table("stock_transactions", schema="homebot")
    op.drop_table("stock", schema="homebot")
