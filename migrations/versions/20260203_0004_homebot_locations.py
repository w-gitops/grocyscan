"""Homebot locations and location_closure (Phase 2).

Revision ID: 0004
Revises: 0003
Create Date: 2026-02-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create homebot.locations and homebot.location_closure."""
    op.create_table(
        "locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("location_type", sa.String(50), nullable=False),
        sa.Column("path", sa.String(1000), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_freezer", sa.Boolean(), nullable=False, server_default=sa.text("false")),
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
        sa.ForeignKeyConstraint(["tenant_id"], ["homebot.tenants.id"], name="fk_homebot_locations_tenant_id"),
        sa.ForeignKeyConstraint(["parent_id"], ["homebot.locations.id"], name="fk_homebot_locations_parent_id"),
        schema="homebot",
    )
    op.create_index("ix_homebot_locations_tenant_id", "locations", ["tenant_id"], schema="homebot")
    op.create_index("ix_homebot_locations_parent_id", "locations", ["parent_id"], schema="homebot")

    op.create_table(
        "location_closure",
        sa.Column("ancestor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("descendant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("depth", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("ancestor_id", "descendant_id"),
        sa.ForeignKeyConstraint(
            ["ancestor_id"],
            ["homebot.locations.id"],
            name="fk_homebot_location_closure_ancestor",
        ),
        sa.ForeignKeyConstraint(
            ["descendant_id"],
            ["homebot.locations.id"],
            name="fk_homebot_location_closure_descendant",
        ),
        schema="homebot",
    )
    op.create_index(
        "ix_homebot_location_closure_descendant",
        "location_closure",
        ["descendant_id"],
        schema="homebot",
    )
    op.create_index(
        "ix_homebot_location_closure_depth",
        "location_closure",
        ["depth"],
        schema="homebot",
    )

    op.execute("ALTER TABLE homebot.locations ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY homebot_locations_tenant_isolation ON homebot.locations
        FOR ALL USING (tenant_id::text = current_setting('app.tenant_id', true))
    """)
    op.execute("ALTER TABLE homebot.location_closure ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY homebot_location_closure_tenant_isolation ON homebot.location_closure
        FOR ALL USING (
            ancestor_id IN (
                SELECT id FROM homebot.locations
                WHERE tenant_id::text = current_setting('app.tenant_id', true)
            )
        )
    """)


def downgrade() -> None:
    """Drop locations and location_closure."""
    op.execute("DROP POLICY IF EXISTS homebot_location_closure_tenant_isolation ON homebot.location_closure")
    op.execute("DROP POLICY IF EXISTS homebot_locations_tenant_isolation ON homebot.locations")
    op.drop_table("location_closure", schema="homebot")
    op.drop_table("locations", schema="homebot")
