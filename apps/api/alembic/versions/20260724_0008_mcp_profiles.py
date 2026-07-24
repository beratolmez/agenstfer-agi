"""Create mcp_profiles table for product-owned approved MCP integration.

Revision ID: 20260724_0008
Revises: 20260713_0007
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260724_0008"
down_revision: str | None = "20260713_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "mcp_profiles",
        sa.Column("id", sa.String(length=120), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("server_identity", sa.String(length=160), nullable=False, index=True),
        sa.Column("transport_type", sa.String(length=40), nullable=False, server_default="stdio"),
        sa.Column("allowed_tools", sa.JSON(), nullable=False),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False, server_default="30"),
        sa.Column(
            "data_classification", sa.String(length=30), nullable=False, server_default="internal"
        ),
        sa.Column("read_only", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("approved", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column(
            "status", sa.String(length=30), nullable=False, server_default="active", index=True
        ),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("mcp_profiles")
