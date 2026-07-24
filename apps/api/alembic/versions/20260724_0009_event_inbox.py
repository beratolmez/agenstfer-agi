"""Create event_inbox and event_dispatch_queue tables.

Revision ID: 20260724_0009
Revises: 20260724_0008
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260724_0009"
down_revision: str | None = "20260724_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "event_inbox",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("source_id", sa.String(length=120), nullable=False, index=True),
        sa.Column("event_type", sa.String(length=120), nullable=False, index=True),
        sa.Column("idempotency_key", sa.String(length=160), nullable=True, index=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "status", sa.String(length=30), nullable=False, server_default="received", index=True
        ),
        sa.Column(
            "matched_rules_count", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "event_dispatch_queue",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column(
            "event_id",
            sa.String(length=80),
            sa.ForeignKey("event_inbox.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("trigger_rule_id", sa.String(length=120), nullable=False, index=True),
        sa.Column("target_workflow_id", sa.String(length=120), nullable=False, index=True),
        sa.Column("target_workflow_version", sa.Integer(), nullable=True),
        sa.Column(
            "status", sa.String(length=30), nullable=False, server_default="queued", index=True
        ),
        sa.Column("workflow_run_id", sa.String(length=36), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("event_dispatch_queue")
    op.drop_table("event_inbox")
