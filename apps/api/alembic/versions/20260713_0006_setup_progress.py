"""Persist single-installation setup progress and validated configuration.

Revision ID: 20260713_0006
Revises: 20260713_0005
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260713_0006"
down_revision: str | None = "20260713_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "installation_state",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("current_step", sa.Integer(), nullable=False),
        sa.Column("completed_steps", sa.JSON(), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_installation_state_status", "installation_state", ["status"])


def downgrade() -> None:
    op.drop_index("ix_installation_state_status", table_name="installation_state")
    op.drop_table("installation_state")
