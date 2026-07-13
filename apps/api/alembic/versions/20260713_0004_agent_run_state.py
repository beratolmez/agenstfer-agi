"""Persist model-assisted diagnostic and agent step state.

Revision ID: 20260713_0004
Revises: 20260713_0003
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260713_0004"
down_revision: str | Sequence[str] | None = "20260713_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for name, column_type in [
        ("input_json", sa.JSON()),
        ("output_json", sa.JSON()),
        ("error_json", sa.JSON()),
        ("model_profile", sa.String(80)),
        ("agent_versions", sa.JSON()),
        ("token_usage", sa.JSON()),
        ("evidence_ids", sa.JSON()),
        ("created_by", sa.String(36)),
    ]:
        op.add_column("workflow_runs", sa.Column(name, column_type, nullable=True))
    op.create_index("ix_workflow_runs_created_by", "workflow_runs", ["created_by"])

    op.create_table(
        "workflow_step_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), sa.ForeignKey("workflow_runs.id"), nullable=False),
        sa.Column("step_id", sa.String(80), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(60), nullable=False),
        sa.Column("agent_id", sa.String(80), nullable=True),
        sa.Column("agent_version", sa.Integer(), nullable=True),
        sa.Column("model_profile", sa.String(80), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("output_json", sa.JSON(), nullable=True),
        sa.Column("error_json", sa.JSON(), nullable=True),
        sa.Column("token_usage", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_workflow_step_runs_run_id", "workflow_step_runs", ["run_id"])
    op.create_index("ix_workflow_step_runs_kind", "workflow_step_runs", ["kind"])
    op.create_index("ix_workflow_step_runs_status", "workflow_step_runs", ["status"])
    op.create_index(
        "ux_step_run_sequence",
        "workflow_step_runs",
        ["run_id", "sequence"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("workflow_step_runs")
    op.drop_index("ix_workflow_runs_created_by", table_name="workflow_runs")
    for name in [
        "created_by",
        "evidence_ids",
        "token_usage",
        "agent_versions",
        "model_profile",
        "error_json",
        "output_json",
        "input_json",
    ]:
        op.drop_column("workflow_runs", name)
