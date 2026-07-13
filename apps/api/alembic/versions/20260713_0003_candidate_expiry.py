"""Add mandatory OKF candidate expiry.

Revision ID: 20260713_0003
Revises: 20260713_0002
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260713_0003"
down_revision: str | Sequence[str] | None = "20260713_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "okf_candidates",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    if op.get_bind().dialect.name == "sqlite":
        op.execute(
            "UPDATE okf_candidates SET expires_at = datetime(created_at, '+7 days') "
            "WHERE expires_at IS NULL"
        )
        with op.batch_alter_table("okf_candidates") as batch:
            batch.alter_column("expires_at", nullable=False)
    else:
        op.execute(
            "UPDATE okf_candidates SET expires_at = created_at + INTERVAL '7 days' "
            "WHERE expires_at IS NULL"
        )
        op.alter_column("okf_candidates", "expires_at", nullable=False)


def downgrade() -> None:
    op.drop_column("okf_candidates", "expires_at")
