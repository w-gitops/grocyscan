"""Homebot devices table (Phase 3 - device registration and preferences).

Revision ID: 0006
Revises: 0005
Create Date: 2026-02-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create homebot.devices for device registration and preferences."""
    op.create_table(
        "devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("fingerprint", sa.String(255), nullable=False),
        sa.Column("device_type", sa.String(50), nullable=False),
        sa.Column("default_location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("default_action", sa.String(50), nullable=False, server_default=sa.text("'add_stock'")),
        sa.Column("scanner_mode", sa.String(50), nullable=False, server_default=sa.text("'camera'")),
        sa.Column("preferences", postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default=sa.text("'{}'")),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["tenant_id"], ["homebot.tenants.id"], name="fk_homebot_devices_tenant_id"),
        sa.ForeignKeyConstraint(["user_id"], ["homebot.users.id"], name="fk_homebot_devices_user_id"),
        sa.ForeignKeyConstraint(
            ["default_location_id"],
            ["homebot.locations.id"],
            name="fk_homebot_devices_default_location_id",
        ),
        schema="homebot",
    )
    op.create_index("ix_homebot_devices_tenant_id", "devices", ["tenant_id"], schema="homebot")
    op.create_index(
        "ix_homebot_devices_tenant_fingerprint",
        "devices",
        ["tenant_id", "fingerprint"],
        unique=True,
        schema="homebot",
    )

    op.execute("ALTER TABLE homebot.devices ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY homebot_devices_tenant_isolation ON homebot.devices
        FOR ALL USING (tenant_id::text = current_setting('app.tenant_id', true))
    """)


def downgrade() -> None:
    """Drop homebot.devices."""
    op.execute("DROP POLICY IF EXISTS homebot_devices_tenant_isolation ON homebot.devices")
    op.drop_table("devices", schema="homebot")
