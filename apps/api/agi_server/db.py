from __future__ import annotations

import uuid
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)

from agi_server.config import get_settings


def utcnow() -> datetime:
    return datetime.now(UTC)


def new_id() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(320), index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(Text)
    roles: Mapped[list[str]] = mapped_column(JSON, default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class InstallationState(Base):
    __tablename__ = "installation_state"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default="default")
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    completed_steps: Mapped[list[int]] = mapped_column(JSON, default=list)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="in_progress", index=True)
    updated_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class DataSource(Base):
    __tablename__ = "data_sources"
    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    connector_type: Mapped[str] = mapped_column(String(60), index=True)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    read_only: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(30), default="configured", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class SourceMapping(Base):
    __tablename__ = "source_mappings"
    source_id: Mapped[str] = mapped_column(ForeignKey("data_sources.id"), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(60), index=True)
    field_mapping: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    validation: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SourceSyncRun(Base):
    __tablename__ = "source_sync_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    source_id: Mapped[str] = mapped_column(ForeignKey("data_sources.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    records_seen: Mapped[int] = mapped_column(Integer, default=0)
    records_persisted: Mapped[int] = mapped_column(Integer, default=0)
    warnings: Mapped[list[str]] = mapped_column(JSON, default=list)
    cursor: Mapped[str | None] = mapped_column(String(180), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RawSnapshotRow(Base):
    __tablename__ = "raw_snapshots"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("data_sources.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    bytes: Mapped[int] = mapped_column(Integer)
    source_type: Mapped[str] = mapped_column(String(60))
    classification: Mapped[str] = mapped_column(String(30), default="internal")
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (Index("ux_raw_snapshot_source_hash", "source_id", "sha256", unique=True),)


class EvidenceItem(Base):
    __tablename__ = "evidence_items"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(120), index=True)
    snapshot_sha256: Mapped[str] = mapped_column(String(64), index=True)
    locator: Mapped[dict[str, Any]] = mapped_column(JSON)
    excerpt_hash: Mapped[str] = mapped_column(String(64))
    classification: Mapped[str] = mapped_column(String(30), default="internal")
    raw_snapshot_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    entity_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (Index("ix_evidence_source_snapshot", "source_id", "snapshot_sha256"),)


class CanonicalEntity(Base):
    __tablename__ = "canonical_entities"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(60), index=True)
    external_keys: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    classification: Mapped[str] = mapped_column(String(30), default="internal", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class CanonicalFact(Base):
    __tablename__ = "canonical_facts"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    subject_id: Mapped[str] = mapped_column(ForeignKey("canonical_entities.id"), index=True)
    predicate: Mapped[str] = mapped_column(String(100), index=True)
    object_entity_id: Mapped[str | None] = mapped_column(
        ForeignKey("canonical_entities.id"), nullable=True, index=True
    )
    value: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    evidence_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    valid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("ix_fact_subject_predicate", "subject_id", "predicate"),)


class WorkflowDefinitionRow(Base):
    __tablename__ = "workflow_definitions"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    version: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(30), index=True)
    definition: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class AgentDefinitionRow(Base):
    __tablename__ = "agent_definitions"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(30), index=True)
    definition: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class CapabilityDefinitionRow(Base):
    __tablename__ = "capability_definitions"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(30), index=True, default="published")
    definition: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WorkflowSchedule(Base):
    __tablename__ = "workflow_schedules"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    workflow_id: Mapped[str] = mapped_column(String(80), index=True)
    workflow_version: Mapped[int]
    cron: Mapped[str] = mapped_column(String(120))
    timezone: Mapped[str] = mapped_column(String(80))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    last_fire_key: Mapped[str | None] = mapped_column(String(180), nullable=True, unique=True)
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    idempotency_key: Mapped[str] = mapped_column(String(180), unique=True)
    workflow_id: Mapped[str] = mapped_column(String(80), index=True)
    workflow_version: Mapped[int]
    status: Mapped[str] = mapped_column(String(30), index=True)
    current_step: Mapped[str | None] = mapped_column(String(80), nullable=True)
    artifact_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    output_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    model_profile: Mapped[str | None] = mapped_column(String(80), nullable=True)
    agent_versions: Mapped[dict[str, int] | None] = mapped_column(JSON, nullable=True)
    token_usage: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    evidence_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approvals: Mapped[list[ApprovalRequest]] = relationship(back_populates="run")


class WorkflowStepRun(Base):
    __tablename__ = "workflow_step_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("workflow_runs.id"), index=True)
    step_id: Mapped[str] = mapped_column(String(80))
    sequence: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(60), index=True)
    agent_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    agent_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model_profile: Mapped[str | None] = mapped_column(String(80), nullable=True)
    model_provider: Mapped[str | None] = mapped_column(String(40), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    data_classification: Mapped[str | None] = mapped_column(String(30), nullable=True)
    redaction_applied: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    input_hash: Mapped[str] = mapped_column(String(64))
    output_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    token_usage: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("ux_step_run_sequence", "run_id", "sequence", unique=True),)


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("workflow_runs.id"), index=True)
    kind: Mapped[str] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(30), index=True, default="pending")
    artifact_uri: Mapped[str] = mapped_column(Text)
    requested_role: Mapped[str] = mapped_column(String(30), default="approver")
    candidate_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    decision_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_idempotency_key: Mapped[str | None] = mapped_column(
        String(180), nullable=True, unique=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    run: Mapped[WorkflowRun] = relationship(back_populates="approvals")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    actor_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    target_type: Mapped[str] = mapped_column(String(80))
    target_id: Mapped[str | None] = mapped_column(String(180), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )


class Artifact(Base):
    __tablename__ = "artifacts"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    run_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String(60), index=True)
    uri: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class OKFCandidate(Base):
    __tablename__ = "okf_candidates"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    run_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)
    base_revision: Mapped[str] = mapped_column(String(64))
    candidate_revision: Mapped[str | None] = mapped_column(String(64), nullable=True)
    worktree_path: Mapped[str] = mapped_column(Text)
    validation_report: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    decided_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MCPProfile(Base):
    __tablename__ = "mcp_profiles"
    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    server_identity: Mapped[str] = mapped_column(String(160), index=True)
    transport_type: Mapped[str] = mapped_column(String(40), default="stdio")
    allowed_tools: Mapped[list[str]] = mapped_column(JSON, default=list)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30)
    data_classification: Mapped[str] = mapped_column(String(30), default="internal")
    read_only: Mapped[bool] = mapped_column(Boolean, default=True)
    approved: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(30), default="active", index=True)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


settings = get_settings()
if settings.database_url.startswith("sqlite"):
    Path("data").mkdir(exist_ok=True)
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
