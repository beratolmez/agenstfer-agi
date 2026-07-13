from __future__ import annotations

import uuid
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, String, Text, create_engine
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
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(Text)
    roles: Mapped[list[str]] = mapped_column(JSON, default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EvidenceItem(Base):
    __tablename__ = "evidence_items"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(120), index=True)
    snapshot_sha256: Mapped[str] = mapped_column(String(64), index=True)
    locator: Mapped[dict[str, Any]] = mapped_column(JSON)
    excerpt_hash: Mapped[str] = mapped_column(String(64))
    classification: Mapped[str] = mapped_column(String(30), default="internal")
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


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    idempotency_key: Mapped[str] = mapped_column(String(180), unique=True)
    workflow_id: Mapped[str] = mapped_column(String(80), index=True)
    workflow_version: Mapped[int]
    status: Mapped[str] = mapped_column(String(30), index=True)
    current_step: Mapped[str | None] = mapped_column(String(80), nullable=True)
    artifact_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approvals: Mapped[list[ApprovalRequest]] = relationship(back_populates="run")


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("workflow_runs.id"), index=True)
    kind: Mapped[str] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(30), index=True, default="pending")
    artifact_uri: Mapped[str] = mapped_column(Text)
    requested_role: Mapped[str] = mapped_column(String(30), default="approver")
    decision_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
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


settings = get_settings()
if settings.database_url.startswith("sqlite"):
    Path("data").mkdir(exist_ok=True)
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(engine)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
