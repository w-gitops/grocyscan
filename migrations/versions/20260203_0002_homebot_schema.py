"""Homebot schema: tenants, users, tenant_memberships with RLS.

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create homebot schema and multi-tenant tables with RLS."""
    op.execute("CREATE SCHEMA IF NOT EXISTS homebot")

    # Tenants table
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("settings", postgresql.JSON(astext_type=sa.Text()), nullable=True),
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
        schema="homebot",
    )
    op.create_index(
        "ix_homebot_tenants_slug",
        "tenants",
        ["slug"],
        unique=True,
        schema="homebot",
    )

    # Users table (in homebot schema; email unique per tenant)
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
            ["tenant_id"],
            ["homebot.tenants.id"],
            name="fk_homebot_users_tenant_id",
        ),
        schema="homebot",
    )
    op.create_index(
        "ix_homebot_users_tenant_id",
        "users",
        ["tenant_id"],
        schema="homebot",
    )
    op.create_index(
        "ix_homebot_users_tenant_email",
        "users",
        ["tenant_id", "email"],
        unique=True,
        schema="homebot",
    )

    # Tenant memberships (user_id, tenant_id, role)
    op.create_table(
        "tenant_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default=sa.text("'member'")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["homebot.users.id"],
            name="fk_homebot_tenant_memberships_user_id",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["homebot.tenants.id"],
            name="fk_homebot_tenant_memberships_tenant_id",
        ),
        schema="homebot",
    )
    op.create_index(
        "ix_homebot_tenant_memberships_user_id",
        "tenant_memberships",
        ["user_id"],
        schema="homebot",
    )
    op.create_index(
        "ix_homebot_tenant_memberships_tenant_id",
        "tenant_memberships",
        ["tenant_id"],
        schema="homebot",
    )
    op.create_index(
        "ix_homebot_tenant_memberships_user_tenant",
        "tenant_memberships",
        ["user_id", "tenant_id"],
        unique=True,
        schema="homebot",
    )

    # Enable RLS on tenants
    op.execute("ALTER TABLE homebot.tenants ENABLE ROW LEVEL SECURITY")
    # Policy: allow SELECT for login (resolve slug -> tenant_id)
    op.execute("""
        CREATE POLICY homebot_tenants_select_for_login ON homebot.tenants
        FOR SELECT
        USING (true)
    """)
    # Policy: allow full access when current_setting('app.tenant_id', true) equals tenant id
    op.execute("""
        CREATE POLICY homebot_tenants_tenant_isolation ON homebot.tenants
        FOR ALL
        USING (id::text = current_setting('app.tenant_id', true))
    """)

    # Enable RLS on users
    op.execute("ALTER TABLE homebot.users ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY homebot_users_tenant_isolation ON homebot.users
        FOR ALL
        USING (tenant_id::text = current_setting('app.tenant_id', true))
    """)

    # Enable RLS on tenant_memberships
    op.execute("ALTER TABLE homebot.tenant_memberships ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY homebot_tenant_memberships_tenant_isolation ON homebot.tenant_memberships
        FOR ALL
        USING (tenant_id::text = current_setting('app.tenant_id', true))
    """)


def downgrade() -> None:
    """Drop homebot schema and RLS policies."""
    op.execute("DROP POLICY IF EXISTS homebot_tenant_memberships_tenant_isolation ON homebot.tenant_memberships")
    op.execute("DROP POLICY IF EXISTS homebot_users_tenant_isolation ON homebot.users")
    op.execute("DROP POLICY IF EXISTS homebot_tenants_tenant_isolation ON homebot.tenants")
    op.execute("DROP POLICY IF EXISTS homebot_tenants_select_for_login ON homebot.tenants")
    op.drop_table("tenant_memberships", schema="homebot")
    op.drop_table("users", schema="homebot")
    op.drop_table("tenants", schema="homebot")
    op.execute("DROP SCHEMA IF EXISTS homebot")
