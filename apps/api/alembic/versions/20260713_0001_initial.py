"""Initial operational, context, evidence and workflow schema.

Revision ID: 20260713_0001
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260713_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("roles", sa.JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "evidence_items",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("source_id", sa.String(120), nullable=False),
        sa.Column("snapshot_sha256", sa.String(64), nullable=False),
        sa.Column("locator", sa.JSON(), nullable=False),
        sa.Column("excerpt_hash", sa.String(64), nullable=False),
        sa.Column("classification", sa.String(30), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_evidence_items_source_id", "evidence_items", ["source_id"])
    op.create_index(
        "ix_evidence_items_snapshot_sha256", "evidence_items", ["snapshot_sha256"]
    )
    op.create_index(
        "ix_evidence_source_snapshot",
        "evidence_items",
        ["source_id", "snapshot_sha256"],
    )

    op.create_table(
        "canonical_entities",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("entity_type", sa.String(60), nullable=False),
        sa.Column("external_keys", sa.JSON(), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=False),
        sa.Column("classification", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_canonical_entities_entity_type", "canonical_entities", ["entity_type"])
    op.create_index(
        "ix_canonical_entities_classification", "canonical_entities", ["classification"]
    )

    op.create_table(
        "workflow_definitions",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("version", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("definition", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_workflow_definitions_status", "workflow_definitions", ["status"]
    )

    op.create_table(
        "workflow_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("idempotency_key", sa.String(180), nullable=False, unique=True),
        sa.Column("workflow_id", sa.String(80), nullable=False),
        sa.Column("workflow_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("current_step", sa.String(80), nullable=True),
        sa.Column("artifact_uri", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_workflow_runs_workflow_id", "workflow_runs", ["workflow_id"])
    op.create_index("ix_workflow_runs_status", "workflow_runs", ["status"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("actor_id", sa.String(36), nullable=True),
        sa.Column("action", sa.String(120), nullable=False),
        sa.Column("target_type", sa.String(80), nullable=False),
        sa.Column("target_id", sa.String(180), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_events_actor_id", "audit_events", ["actor_id"])
    op.create_index("ix_audit_events_action", "audit_events", ["action"])
    op.create_index("ix_audit_events_occurred_at", "audit_events", ["occurred_at"])

    op.create_table(
        "canonical_facts",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column(
            "subject_id", sa.String(80), sa.ForeignKey("canonical_entities.id"), nullable=False
        ),
        sa.Column("predicate", sa.String(100), nullable=False),
        sa.Column(
            "object_entity_id",
            sa.String(80),
            sa.ForeignKey("canonical_entities.id"),
            nullable=True,
        ),
        sa.Column("value", sa.JSON(), nullable=True),
        sa.Column("evidence_ids", sa.JSON(), nullable=False),
        sa.Column("valid_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_canonical_facts_subject_id", "canonical_facts", ["subject_id"])
    op.create_index("ix_canonical_facts_predicate", "canonical_facts", ["predicate"])
    op.create_index(
        "ix_canonical_facts_object_entity_id", "canonical_facts", ["object_entity_id"]
    )
    op.create_index(
        "ix_fact_subject_predicate", "canonical_facts", ["subject_id", "predicate"]
    )

    op.create_table(
        "approval_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), sa.ForeignKey("workflow_runs.id"), nullable=False),
        sa.Column("kind", sa.String(60), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("artifact_uri", sa.Text(), nullable=False),
        sa.Column("requested_role", sa.String(30), nullable=False),
        sa.Column("decision_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_approval_requests_run_id", "approval_requests", ["run_id"])
    op.create_index("ix_approval_requests_status", "approval_requests", ["status"])


def downgrade() -> None:
    op.drop_table("approval_requests")
    op.drop_table("canonical_facts")
    op.drop_table("audit_events")
    op.drop_table("workflow_runs")
    op.drop_table("workflow_definitions")
    op.drop_table("canonical_entities")
    op.drop_table("evidence_items")
    op.drop_table("users")
