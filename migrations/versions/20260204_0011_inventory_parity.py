"""Homebot Inventory Parity (Phase 3.5).

Revision ID: 0011
Revises: 0010
Create Date: 2026-02-04

Adds:
- quantity_units table
- quantity_unit_conversions table
- product_groups table
- Product quantity unit FKs and best-before settings
- Product advanced fields (parent, default locations, tare weight, etc.)
- Stock entry enhancements (decimal quantity, stock_id, price, open, note)
- Transaction log enhancements (user_id, product_id, correlation_id, undone)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create tables and add columns for inventory parity."""
    # 1. Create quantity_units table
    op.create_table(
        "quantity_units",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("name_plural", sa.String(100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["homebot.tenants.id"], name="fk_homebot_qu_tenant_id"),
        schema="homebot",
    )
    op.create_index("ix_homebot_quantity_units_tenant_id", "quantity_units", ["tenant_id"], schema="homebot")
    op.execute("ALTER TABLE homebot.quantity_units ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY homebot_quantity_units_tenant_isolation ON homebot.quantity_units
        FOR ALL USING (tenant_id::text = current_setting('app.tenant_id', true))
    """)

    # 2. Create product_groups table
    op.create_table(
        "product_groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["homebot.tenants.id"], name="fk_homebot_pg_tenant_id"),
        schema="homebot",
    )
    op.create_index("ix_homebot_product_groups_tenant_id", "product_groups", ["tenant_id"], schema="homebot")
    op.execute("ALTER TABLE homebot.product_groups ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY homebot_product_groups_tenant_isolation ON homebot.product_groups
        FOR ALL USING (tenant_id::text = current_setting('app.tenant_id', true))
    """)

    # 3. Add columns to products table
    # Quantity unit FKs
    op.add_column("products", sa.Column("qu_id_purchase", postgresql.UUID(as_uuid=True), nullable=True), schema="homebot")
    op.add_column("products", sa.Column("qu_id_stock", postgresql.UUID(as_uuid=True), nullable=True), schema="homebot")
    op.add_column("products", sa.Column("qu_id_consume", postgresql.UUID(as_uuid=True), nullable=True), schema="homebot")
    op.create_foreign_key("fk_homebot_products_qu_purchase", "products", "quantity_units",
                          ["qu_id_purchase"], ["id"], source_schema="homebot", referent_schema="homebot")
    op.create_foreign_key("fk_homebot_products_qu_stock", "products", "quantity_units",
                          ["qu_id_stock"], ["id"], source_schema="homebot", referent_schema="homebot")
    op.create_foreign_key("fk_homebot_products_qu_consume", "products", "quantity_units",
                          ["qu_id_consume"], ["id"], source_schema="homebot", referent_schema="homebot")

    # Best-before settings
    op.add_column("products", sa.Column("default_best_before_days", sa.Integer(), nullable=True), schema="homebot")
    op.add_column("products", sa.Column("default_best_before_days_after_open", sa.Integer(), nullable=True), schema="homebot")
    op.add_column("products", sa.Column("default_best_before_days_after_freezing", sa.Integer(), nullable=True), schema="homebot")
    op.add_column("products", sa.Column("default_best_before_days_after_thawing", sa.Integer(), nullable=True), schema="homebot")
    op.add_column("products", sa.Column("due_type", sa.Integer(), server_default=sa.text("1"), nullable=False), schema="homebot")

    # Advanced fields
    op.add_column("products", sa.Column("parent_product_id", postgresql.UUID(as_uuid=True), nullable=True), schema="homebot")
    op.add_column("products", sa.Column("product_group_id", postgresql.UUID(as_uuid=True), nullable=True), schema="homebot")
    op.add_column("products", sa.Column("default_location_id", postgresql.UUID(as_uuid=True), nullable=True), schema="homebot")
    op.add_column("products", sa.Column("default_consume_location_id", postgresql.UUID(as_uuid=True), nullable=True), schema="homebot")
    op.add_column("products", sa.Column("tare_weight", sa.Numeric(15, 4), nullable=True), schema="homebot")
    op.add_column("products", sa.Column("enable_tare_weight_handling", sa.Boolean(), server_default=sa.text("false"), nullable=False), schema="homebot")
    op.add_column("products", sa.Column("calories", sa.Integer(), nullable=True), schema="homebot")
    op.add_column("products", sa.Column("quick_consume_amount", sa.Numeric(15, 4), server_default=sa.text("1"), nullable=False), schema="homebot")
    op.add_column("products", sa.Column("move_on_open", sa.Boolean(), server_default=sa.text("false"), nullable=False), schema="homebot")
    op.add_column("products", sa.Column("should_not_be_frozen", sa.Boolean(), server_default=sa.text("false"), nullable=False), schema="homebot")

    op.create_foreign_key("fk_homebot_products_parent", "products", "products",
                          ["parent_product_id"], ["id"], source_schema="homebot", referent_schema="homebot")
    op.create_foreign_key("fk_homebot_products_group", "products", "product_groups",
                          ["product_group_id"], ["id"], source_schema="homebot", referent_schema="homebot")
    op.create_foreign_key("fk_homebot_products_default_loc", "products", "locations",
                          ["default_location_id"], ["id"], source_schema="homebot", referent_schema="homebot")
    op.create_foreign_key("fk_homebot_products_consume_loc", "products", "locations",
                          ["default_consume_location_id"], ["id"], source_schema="homebot", referent_schema="homebot")

    # 4. Create quantity_unit_conversions table
    op.create_table(
        "quantity_unit_conversions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),  # NULL = global conversion
        sa.Column("from_qu_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("to_qu_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("factor", sa.Numeric(15, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["homebot.tenants.id"], name="fk_homebot_quc_tenant_id"),
        sa.ForeignKeyConstraint(["product_id"], ["homebot.products.id"], name="fk_homebot_quc_product_id"),
        sa.ForeignKeyConstraint(["from_qu_id"], ["homebot.quantity_units.id"], name="fk_homebot_quc_from_qu"),
        sa.ForeignKeyConstraint(["to_qu_id"], ["homebot.quantity_units.id"], name="fk_homebot_quc_to_qu"),
        schema="homebot",
    )
    op.create_index("ix_homebot_quc_tenant_id", "quantity_unit_conversions", ["tenant_id"], schema="homebot")
    op.create_index("ix_homebot_quc_product_id", "quantity_unit_conversions", ["product_id"], schema="homebot")
    op.execute("ALTER TABLE homebot.quantity_unit_conversions ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY homebot_quc_tenant_isolation ON homebot.quantity_unit_conversions
        FOR ALL USING (tenant_id::text = current_setting('app.tenant_id', true))
    """)

    # 5. Stock entry enhancements
    # Change quantity from INTEGER to DECIMAL(15,2)
    op.execute("ALTER TABLE homebot.stock ALTER COLUMN quantity TYPE DECIMAL(15,2) USING quantity::decimal(15,2)")

    # Add new columns
    op.add_column("stock", sa.Column("stock_id", sa.String(36), nullable=True), schema="homebot")
    op.add_column("stock", sa.Column("purchased_date", sa.Date(), nullable=True), schema="homebot")
    op.add_column("stock", sa.Column("price", sa.Numeric(13, 2), nullable=True), schema="homebot")
    op.add_column("stock", sa.Column("open", sa.Boolean(), server_default=sa.text("false"), nullable=False), schema="homebot")
    op.add_column("stock", sa.Column("opened_date", sa.Date(), nullable=True), schema="homebot")
    op.add_column("stock", sa.Column("note", sa.Text(), nullable=True), schema="homebot")
    op.add_column("stock", sa.Column("shopping_location_id", postgresql.UUID(as_uuid=True), nullable=True), schema="homebot")
    op.create_foreign_key("fk_homebot_stock_shopping_loc", "stock", "locations",
                          ["shopping_location_id"], ["id"], source_schema="homebot", referent_schema="homebot")
    op.create_index("ix_homebot_stock_stock_id", "stock", ["stock_id"], unique=True, schema="homebot")

    # Generate stock_id for existing entries
    op.execute("""
        UPDATE homebot.stock SET stock_id = gen_random_uuid()::text WHERE stock_id IS NULL
    """)

    # 6. Transaction log enhancements
    # Change quantity from INTEGER to DECIMAL(15,2)
    op.execute("ALTER TABLE homebot.stock_transactions ALTER COLUMN quantity TYPE DECIMAL(15,2) USING quantity::decimal(15,2)")

    op.add_column("stock_transactions", sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True), schema="homebot")
    op.add_column("stock_transactions", sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True), schema="homebot")
    op.add_column("stock_transactions", sa.Column("spoiled", sa.Boolean(), server_default=sa.text("false"), nullable=False), schema="homebot")
    op.add_column("stock_transactions", sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=True), schema="homebot")
    op.add_column("stock_transactions", sa.Column("transaction_id", postgresql.UUID(as_uuid=True), nullable=True), schema="homebot")
    op.add_column("stock_transactions", sa.Column("undone", sa.Boolean(), server_default=sa.text("false"), nullable=False), schema="homebot")
    op.add_column("stock_transactions", sa.Column("undone_timestamp", sa.DateTime(timezone=True), nullable=True), schema="homebot")

    op.create_foreign_key("fk_homebot_stock_tx_product_id", "stock_transactions", "products",
                          ["product_id"], ["id"], source_schema="homebot", referent_schema="homebot")
    op.create_index("ix_homebot_stock_tx_correlation_id", "stock_transactions", ["correlation_id"], schema="homebot")
    op.create_index("ix_homebot_stock_tx_product_id", "stock_transactions", ["product_id"], schema="homebot")

    # Seed default quantity units
    op.execute("""
        INSERT INTO homebot.quantity_units (tenant_id, name, name_plural, description)
        SELECT id, 'Piece', 'Pieces', 'Individual items'
        FROM homebot.tenants WHERE id = (SELECT id FROM homebot.tenants LIMIT 1)
        ON CONFLICT DO NOTHING
    """)


def downgrade() -> None:
    """Remove inventory parity additions."""
    # Remove foreign keys first
    op.drop_constraint("fk_homebot_stock_tx_product_id", "stock_transactions", schema="homebot", type_="foreignkey")
    op.drop_index("ix_homebot_stock_tx_correlation_id", table_name="stock_transactions", schema="homebot")
    op.drop_index("ix_homebot_stock_tx_product_id", table_name="stock_transactions", schema="homebot")

    # Remove transaction log enhancements
    op.drop_column("stock_transactions", "undone_timestamp", schema="homebot")
    op.drop_column("stock_transactions", "undone", schema="homebot")
    op.drop_column("stock_transactions", "transaction_id", schema="homebot")
    op.drop_column("stock_transactions", "correlation_id", schema="homebot")
    op.drop_column("stock_transactions", "spoiled", schema="homebot")
    op.drop_column("stock_transactions", "product_id", schema="homebot")
    op.drop_column("stock_transactions", "user_id", schema="homebot")
    op.execute("ALTER TABLE homebot.stock_transactions ALTER COLUMN quantity TYPE INTEGER USING quantity::integer")

    # Remove stock entry enhancements
    op.drop_constraint("fk_homebot_stock_shopping_loc", "stock", schema="homebot", type_="foreignkey")
    op.drop_index("ix_homebot_stock_stock_id", table_name="stock", schema="homebot")
    op.drop_column("stock", "shopping_location_id", schema="homebot")
    op.drop_column("stock", "note", schema="homebot")
    op.drop_column("stock", "opened_date", schema="homebot")
    op.drop_column("stock", "open", schema="homebot")
    op.drop_column("stock", "price", schema="homebot")
    op.drop_column("stock", "purchased_date", schema="homebot")
    op.drop_column("stock", "stock_id", schema="homebot")
    op.execute("ALTER TABLE homebot.stock ALTER COLUMN quantity TYPE INTEGER USING quantity::integer")

    # Remove quantity_unit_conversions
    op.execute("DROP POLICY IF EXISTS homebot_quc_tenant_isolation ON homebot.quantity_unit_conversions")
    op.drop_table("quantity_unit_conversions", schema="homebot")

    # Remove product columns
    op.drop_constraint("fk_homebot_products_consume_loc", "products", schema="homebot", type_="foreignkey")
    op.drop_constraint("fk_homebot_products_default_loc", "products", schema="homebot", type_="foreignkey")
    op.drop_constraint("fk_homebot_products_group", "products", schema="homebot", type_="foreignkey")
    op.drop_constraint("fk_homebot_products_parent", "products", schema="homebot", type_="foreignkey")
    op.drop_column("products", "should_not_be_frozen", schema="homebot")
    op.drop_column("products", "move_on_open", schema="homebot")
    op.drop_column("products", "quick_consume_amount", schema="homebot")
    op.drop_column("products", "calories", schema="homebot")
    op.drop_column("products", "enable_tare_weight_handling", schema="homebot")
    op.drop_column("products", "tare_weight", schema="homebot")
    op.drop_column("products", "default_consume_location_id", schema="homebot")
    op.drop_column("products", "default_location_id", schema="homebot")
    op.drop_column("products", "product_group_id", schema="homebot")
    op.drop_column("products", "parent_product_id", schema="homebot")
    op.drop_column("products", "due_type", schema="homebot")
    op.drop_column("products", "default_best_before_days_after_thawing", schema="homebot")
    op.drop_column("products", "default_best_before_days_after_freezing", schema="homebot")
    op.drop_column("products", "default_best_before_days_after_open", schema="homebot")
    op.drop_column("products", "default_best_before_days", schema="homebot")
    op.drop_constraint("fk_homebot_products_qu_consume", "products", schema="homebot", type_="foreignkey")
    op.drop_constraint("fk_homebot_products_qu_stock", "products", schema="homebot", type_="foreignkey")
    op.drop_constraint("fk_homebot_products_qu_purchase", "products", schema="homebot", type_="foreignkey")
    op.drop_column("products", "qu_id_consume", schema="homebot")
    op.drop_column("products", "qu_id_stock", schema="homebot")
    op.drop_column("products", "qu_id_purchase", schema="homebot")

    # Remove product_groups
    op.execute("DROP POLICY IF EXISTS homebot_product_groups_tenant_isolation ON homebot.product_groups")
    op.drop_table("product_groups", schema="homebot")

    # Remove quantity_units
    op.execute("DROP POLICY IF EXISTS homebot_quantity_units_tenant_isolation ON homebot.quantity_units")
    op.drop_table("quantity_units", schema="homebot")
