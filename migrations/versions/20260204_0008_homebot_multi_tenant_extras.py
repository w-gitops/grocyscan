"""Homebot multi-tenant extras: roles, qr namespaces, service tokens.

Revision ID: 0011
Revises: 0010
Create Date: 2026-02-04
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
    """Create roles and Phase 1 multi-tenant tables."""
    # Roles (best-effort; may require elevated privileges)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
                CREATE ROLE app_user;
            END IF;
        EXCEPTION
            WHEN insufficient_privilege THEN
                RAISE NOTICE 'Skipping app_user role creation (insufficient privilege).';
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'migration_user') THEN
                CREATE ROLE migration_user BYPASSRLS;
            END IF;
        EXCEPTION
            WHEN insufficient_privilege THEN
                RAISE NOTICE 'Skipping migration_user role creation (insufficient privilege).';
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
                EXECUTE 'GRANT USAGE ON SCHEMA homebot TO app_user';
                EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA homebot TO app_user';
                EXECUTE 'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA homebot TO app_user';
            END IF;
        EXCEPTION
            WHEN insufficient_privilege THEN
                RAISE NOTICE 'Skipping grants for app_user (insufficient privilege).';
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'migration_user') THEN
                EXECUTE 'GRANT USAGE ON SCHEMA homebot TO migration_user';
                EXECUTE 'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA homebot TO migration_user';
                EXECUTE 'GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA homebot TO migration_user';
            END IF;
        EXCEPTION
            WHEN insufficient_privilege THEN
                RAISE NOTICE 'Skipping grants for migration_user (insufficient privilege).';
        END $$;
        """
    )

    # QR namespaces (Phase 1 multi-tenant groundwork)
    op.create_table(
        "qr_namespaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(4), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["homebot.tenants.id"],
            name="fk_homebot_qr_namespaces_tenant_id",
        ),
        schema="homebot",
    )
    op.create_index(
        "ix_homebot_qr_namespaces_tenant_id",
        "qr_namespaces",
        ["tenant_id"],
        schema="homebot",
    )
    op.create_index(
        "ix_homebot_qr_namespaces_code",
        "qr_namespaces",
        ["code"],
        unique=True,
        schema="homebot",
    )
    op.execute("ALTER TABLE homebot.qr_namespaces ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY homebot_qr_namespaces_tenant_isolation ON homebot.qr_namespaces
        FOR ALL USING (tenant_id::text = current_setting('app.tenant_id', true))
        """
    )

    # Service accounts (tenant-bound API keys)
    op.create_table(
        "service_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["homebot.tenants.id"],
            name="fk_homebot_service_accounts_tenant_id",
        ),
        schema="homebot",
    )
    op.create_index(
        "ix_homebot_service_accounts_tenant_id",
        "service_accounts",
        ["tenant_id"],
        schema="homebot",
    )
    op.execute("ALTER TABLE homebot.service_accounts ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY homebot_service_accounts_tenant_isolation ON homebot.service_accounts
        FOR ALL USING (tenant_id::text = current_setting('app.tenant_id', true))
        """
    )

    # Service tokens (bcrypt-hashed, tenant-scoped via service_accounts)
    op.create_table(
        "service_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("service_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("scopes", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["service_account_id"],
            ["homebot.service_accounts.id"],
            name="fk_homebot_service_tokens_account_id",
        ),
        schema="homebot",
    )
    op.create_index(
        "ix_homebot_service_tokens_account_id",
        "service_tokens",
        ["service_account_id"],
        schema="homebot",
    )
    op.execute("ALTER TABLE homebot.service_tokens ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY homebot_service_tokens_tenant_isolation ON homebot.service_tokens
        FOR ALL USING (
            service_account_id IN (
                SELECT id FROM homebot.service_accounts
                WHERE tenant_id::text = current_setting('app.tenant_id', true)
            )
        )
        """
    )


def downgrade() -> None:
    """Drop Phase 1 multi-tenant extras."""
    op.execute("DROP POLICY IF EXISTS homebot_service_tokens_tenant_isolation ON homebot.service_tokens")
    op.execute("DROP POLICY IF EXISTS homebot_service_accounts_tenant_isolation ON homebot.service_accounts")
    op.execute("DROP POLICY IF EXISTS homebot_qr_namespaces_tenant_isolation ON homebot.qr_namespaces")
    op.drop_table("service_tokens", schema="homebot")
    op.drop_table("service_accounts", schema="homebot")
    op.drop_table("qr_namespaces", schema="homebot")
    # Roles and grants are not dropped to avoid impacting existing deployments.
