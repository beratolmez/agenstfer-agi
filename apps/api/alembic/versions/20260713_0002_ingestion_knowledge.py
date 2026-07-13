"""Persistent source, snapshot, artifact and OKF candidate schema.

Revision ID: 20260713_0002
Revises: 20260713_0001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260713_0002"
down_revision: str | Sequence[str] | None = "20260713_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "data_sources",
        sa.Column("id", sa.String(120), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("connector_type", sa.String(60), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("read_only", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_data_sources_connector_type", "data_sources", ["connector_type"])
    op.create_index("ix_data_sources_status", "data_sources", ["status"])

    op.create_table(
        "source_mappings",
        sa.Column("source_id", sa.String(120), sa.ForeignKey("data_sources.id"), primary_key=True),
        sa.Column("version", sa.Integer(), primary_key=True),
        sa.Column("entity_type", sa.String(60), nullable=False),
        sa.Column("field_mapping", sa.JSON(), nullable=False),
        sa.Column("validation", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_source_mappings_entity_type", "source_mappings", ["entity_type"])

    op.create_table(
        "source_sync_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_id", sa.String(120), sa.ForeignKey("data_sources.id"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("records_seen", sa.Integer(), nullable=False),
        sa.Column("records_persisted", sa.Integer(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("cursor", sa.String(180), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_source_sync_runs_source_id", "source_sync_runs", ["source_id"])
    op.create_index("ix_source_sync_runs_status", "source_sync_runs", ["status"])

    op.create_table(
        "raw_snapshots",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("source_id", sa.String(120), sa.ForeignKey("data_sources.id"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("bytes", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(60), nullable=False),
        sa.Column("classification", sa.String(30), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_raw_snapshots_source_id", "raw_snapshots", ["source_id"])
    op.create_index("ix_raw_snapshots_sha256", "raw_snapshots", ["sha256"])
    op.create_index(
        "ux_raw_snapshot_source_hash", "raw_snapshots", ["source_id", "sha256"], unique=True
    )

    op.add_column("evidence_items", sa.Column("raw_snapshot_id", sa.String(80), nullable=True))
    op.add_column("evidence_items", sa.Column("entity_id", sa.String(80), nullable=True))
    op.create_index("ix_evidence_items_raw_snapshot_id", "evidence_items", ["raw_snapshot_id"])
    op.create_index("ix_evidence_items_entity_id", "evidence_items", ["entity_id"])

    op.create_table(
        "artifacts",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("run_id", sa.String(36), nullable=True),
        sa.Column("kind", sa.String(60), nullable=False),
        sa.Column("uri", sa.Text(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_artifacts_run_id", "artifacts", ["run_id"])
    op.create_index("ix_artifacts_kind", "artifacts", ["kind"])
    op.create_index("ix_artifacts_sha256", "artifacts", ["sha256"])

    op.create_table(
        "okf_candidates",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("run_id", sa.String(36), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("base_revision", sa.String(64), nullable=False),
        sa.Column("candidate_revision", sa.String(64), nullable=True),
        sa.Column("worktree_path", sa.Text(), nullable=False),
        sa.Column("validation_report", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("decided_by", sa.String(36), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_okf_candidates_run_id", "okf_candidates", ["run_id"])
    op.create_index("ix_okf_candidates_status", "okf_candidates", ["status"])


def downgrade() -> None:
    op.drop_table("okf_candidates")
    op.drop_table("artifacts")
    op.drop_index("ix_evidence_items_entity_id", table_name="evidence_items")
    op.drop_index("ix_evidence_items_raw_snapshot_id", table_name="evidence_items")
    op.drop_column("evidence_items", "entity_id")
    op.drop_column("evidence_items", "raw_snapshot_id")
    op.drop_table("raw_snapshots")
    op.drop_table("source_sync_runs")
    op.drop_table("source_mappings")
    op.drop_table("data_sources")
