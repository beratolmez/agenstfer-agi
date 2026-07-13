"""Versioned agent, capability, workflow schedule and approval state.

Revision ID: 20260713_0005
Revises: 20260713_0004
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260713_0005"
down_revision: str | None = "20260713_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "workflow_definitions",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute("UPDATE workflow_definitions SET updated_at = created_at")
    with op.batch_alter_table("workflow_definitions") as batch:
        batch.alter_column("updated_at", nullable=False)

    op.create_table(
        "agent_definitions",
        sa.Column("id", sa.String(length=80), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("definition", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id", "version"),
    )
    op.create_index("ix_agent_definitions_status", "agent_definitions", ["status"])
    op.create_table(
        "capability_definitions",
        sa.Column("id", sa.String(length=100), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("definition", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", "version"),
    )
    op.create_index("ix_capability_definitions_status", "capability_definitions", ["status"])
    op.create_table(
        "workflow_schedules",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("workflow_id", sa.String(length=80), nullable=False),
        sa.Column("workflow_version", sa.Integer(), nullable=False),
        sa.Column("cron", sa.String(length=120), nullable=False),
        sa.Column("timezone", sa.String(length=80), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("last_fire_key", sa.String(length=180), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("last_fire_key"),
    )
    op.create_index("ix_workflow_schedules_enabled", "workflow_schedules", ["enabled"])
    op.create_index("ix_workflow_schedules_workflow_id", "workflow_schedules", ["workflow_id"])
    with op.batch_alter_table("approval_requests") as batch:
        batch.add_column(sa.Column("candidate_id", sa.String(length=80), nullable=True))
        batch.add_column(
            sa.Column("decision_idempotency_key", sa.String(length=180), nullable=True)
        )
        batch.create_unique_constraint(
            "uq_approval_decision_idempotency", ["decision_idempotency_key"]
        )
    op.create_index("ix_approval_requests_candidate_id", "approval_requests", ["candidate_id"])


def downgrade() -> None:
    op.drop_index("ix_approval_requests_candidate_id", table_name="approval_requests")
    with op.batch_alter_table("approval_requests") as batch:
        batch.drop_constraint("uq_approval_decision_idempotency", type_="unique")
        batch.drop_column("decision_idempotency_key")
        batch.drop_column("candidate_id")
    op.drop_index("ix_workflow_schedules_workflow_id", table_name="workflow_schedules")
    op.drop_index("ix_workflow_schedules_enabled", table_name="workflow_schedules")
    op.drop_table("workflow_schedules")
    op.drop_index("ix_capability_definitions_status", table_name="capability_definitions")
    op.drop_table("capability_definitions")
    op.drop_index("ix_agent_definitions_status", table_name="agent_definitions")
    op.drop_table("agent_definitions")
    op.drop_column("workflow_definitions", "updated_at")
