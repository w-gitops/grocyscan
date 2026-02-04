"""Homebot people table for household profiles.

Revision ID: 0010
Revises: 0009
Create Date: 2026-02-04

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
    """Create homebot.people with RLS."""
    op.create_table(
        "people",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("nickname", sa.String(50), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("color", sa.String(7), nullable=True),
        sa.Column("dietary_restrictions", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("allergies", postgresql.ARRAY(sa.String()), nullable=True),
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
            name="fk_homebot_people_tenant_id",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["homebot.users.id"],
            name="fk_homebot_people_user_id",
        ),
        schema="homebot",
    )
    op.create_index(
        "ix_homebot_people_tenant_id",
        "people",
        ["tenant_id"],
        schema="homebot",
    )
    op.create_index(
        "ix_homebot_people_user_id",
        "people",
        ["user_id"],
        schema="homebot",
    )
    op.create_index(
        "ix_homebot_people_active",
        "people",
        ["tenant_id", "is_active"],
        schema="homebot",
    )

    op.execute("ALTER TABLE homebot.people ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY homebot_people_tenant_isolation ON homebot.people
        FOR ALL USING (tenant_id::text = current_setting('app.tenant_id', true))
        """
    )


def downgrade() -> None:
    """Drop homebot.people."""
    op.execute("DROP POLICY IF EXISTS homebot_people_tenant_isolation ON homebot.people")
    op.drop_table("people", schema="homebot")
