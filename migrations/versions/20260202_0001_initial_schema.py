"""Initial database schema.

Revision ID: 0001
Revises:
Create Date: 2026-02-02

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all initial tables."""
    # Users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("is_admin", sa.Boolean(), nullable=False, default=False),
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
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # Products table
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("grocy_product_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("name_normalized", sa.String(500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(255), nullable=True),
        sa.Column("quantity_unit", sa.String(50), nullable=True),
        sa.Column("image_path", sa.String(500), nullable=True),
        sa.Column("image_uploaded_to_grocy", sa.Boolean(), nullable=False, default=False),
        sa.Column("nutrition_json", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("llm_optimized", sa.Boolean(), nullable=False, default=False),
        sa.Column("raw_lookup_data", postgresql.JSON(astext_type=sa.Text()), nullable=True),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_products_user_id", "products", ["user_id"])
    op.create_index("ix_products_grocy_product_id", "products", ["grocy_product_id"])
    op.create_index("ix_products_name_normalized", "products", ["name_normalized"])
    op.create_index("ix_products_category", "products", ["category"])
    op.create_index(
        "ix_products_user_name_normalized", "products", ["user_id", "name_normalized"]
    )
    op.create_index(
        "ix_products_user_grocy_id", "products", ["user_id", "grocy_product_id"]
    )

    # Barcodes table
    op.create_table(
        "barcodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("barcode", sa.String(100), nullable=False),
        sa.Column("barcode_type", sa.String(20), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, default=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_barcodes_user_id", "barcodes", ["user_id"])
    op.create_index("ix_barcodes_product_id", "barcodes", ["product_id"])
    op.create_index(
        "ix_barcodes_user_barcode", "barcodes", ["user_id", "barcode"], unique=True
    )

    # Locations table
    op.create_table(
        "locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("grocy_location_id", sa.Integer(), nullable=True),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_freezer", sa.Boolean(), nullable=False, default=False),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_locations_user_id", "locations", ["user_id"])
    op.create_index("ix_locations_grocy_location_id", "locations", ["grocy_location_id"])
    op.create_index(
        "ix_locations_user_code", "locations", ["user_id", "code"], unique=True
    )

    # Stock entries table
    op.create_table(
        "stock_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("grocy_stock_id", sa.Integer(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False, default=1),
        sa.Column("best_before", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "purchased_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("price", sa.String(20), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("synced_to_grocy", sa.Boolean(), nullable=False, default=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stock_entries_user_id", "stock_entries", ["user_id"])
    op.create_index("ix_stock_entries_product_id", "stock_entries", ["product_id"])
    op.create_index("ix_stock_entries_location_id", "stock_entries", ["location_id"])
    op.create_index("ix_stock_entries_best_before", "stock_entries", ["best_before"])
    op.create_index(
        "ix_stock_entries_user_best_before",
        "stock_entries",
        ["user_id", "best_before"],
    )

    # Lookup cache table
    op.create_table(
        "lookup_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("barcode", sa.String(100), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("response_json", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("optimized_json", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("image_url", sa.String(1000), nullable=True),
        sa.Column("image_local_path", sa.String(500), nullable=True),
        sa.Column("lookup_success", sa.Boolean(), nullable=False, default=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lookup_cache_barcode", "lookup_cache", ["barcode"])
    op.create_index("ix_lookup_cache_expires_at", "lookup_cache", ["expires_at"])
    op.create_index(
        "ix_lookup_cache_barcode_provider",
        "lookup_cache",
        ["barcode", "provider"],
        unique=True,
    )

    # Jobs table
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, default="pending"),
        sa.Column("priority", sa.Integer(), nullable=False, default=0),
        sa.Column("payload_json", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("result_json", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, default=0),
        sa.Column("max_attempts", sa.Integer(), nullable=False, default=3),
        sa.Column(
            "scheduled_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_jobs_user_id", "jobs", ["user_id"])
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_index("ix_jobs_priority", "jobs", ["priority"])
    op.create_index(
        "ix_jobs_status_priority_scheduled",
        "jobs",
        ["status", "priority", "scheduled_at"],
    )

    # Scan history table
    op.create_table(
        "scan_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("barcode", sa.String(100), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("input_method", sa.String(20), nullable=True),
        sa.Column("best_before", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lookup_provider", sa.String(50), nullable=True),
        sa.Column("lookup_duration_ms", sa.Integer(), nullable=True),
        sa.Column("llm_optimized", sa.Boolean(), nullable=False, default=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scan_history_user_id", "scan_history", ["user_id"])
    op.create_index("ix_scan_history_barcode", "scan_history", ["barcode"])
    op.create_index(
        "ix_scan_history_user_created", "scan_history", ["user_id", "created_at"]
    )

    # Settings table
    op.create_table(
        "settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value_json", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_settings_user_id", "settings", ["user_id"])
    op.create_index(
        "ix_settings_user_key", "settings", ["user_id", "key"], unique=True
    )


def downgrade() -> None:
    """Drop all tables in reverse order."""
    op.drop_table("settings")
    op.drop_table("scan_history")
    op.drop_table("jobs")
    op.drop_table("lookup_cache")
    op.drop_table("stock_entries")
    op.drop_table("locations")
    op.drop_table("barcodes")
    op.drop_table("products")
    op.drop_table("users")
