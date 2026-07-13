from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy.orm import Session

from agi_server.db import Artifact, OKFCandidate, RawSnapshotRow
from agi_server.domain.diagnostic import build_growth_diagnostic
from agi_server.okf.bundle import FileSystemOKFBundle
from agi_server.okf.compiler import compile_demo_bundle
from agi_server.okf.git_repo import GitKnowledgeRepository


def _source_metadata(db: Session) -> dict[str, dict[str, Any]]:
    snapshots = db.query(RawSnapshotRow).order_by(RawSnapshotRow.collected_at.desc()).all()
    result: dict[str, dict[str, Any]] = {}
    for snapshot in snapshots:
        result.setdefault(
            snapshot.source_id,
            {
                "snapshot_id": snapshot.id,
                "snapshot_sha256": snapshot.sha256,
                "collected_at": snapshot.collected_at.isoformat(),
            },
        )
    return result


def ensure_active_repository(active_root: Path | str) -> str:
    bundle = FileSystemOKFBundle(active_root)
    bundle.create("Company Knowledge Bundle")
    return GitKnowledgeRepository(active_root).ensure_baseline()


def create_demo_candidate(
    db: Session,
    active_root: Path | str,
    candidates_root: Path | str,
    actor_id: str | None,
    run_id: str | None = None,
    diagnostic=None,
) -> tuple[OKFCandidate, str]:
    candidate_id = f"candidate-{uuid.uuid4()}"
    repository = GitKnowledgeRepository(active_root)
    destination = Path(candidates_root).resolve() / candidate_id
    diagnostic = diagnostic or build_growth_diagnostic(db)
    metadata = _source_metadata(db)

    def build(worktree: Path) -> None:
        bundle = compile_demo_bundle(
            worktree,
            diagnostic=diagnostic,
            source_metadata=metadata,
        )
        if not bundle.validate().valid:
            raise ValueError("Generated OKF candidate is not conformant")

    git_candidate = repository.create_candidate(candidate_id, destination, build)
    report = FileSystemOKFBundle(destination).validate()
    row = OKFCandidate(
        id=candidate_id,
        run_id=run_id,
        status="pending",
        base_revision=git_candidate.base_revision,
        candidate_revision=git_candidate.candidate_revision,
        worktree_path=str(destination),
        validation_report=report.model_dump(mode="json"),
        created_by=actor_id,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(row)
    db.add(
        Artifact(
            id=f"artifact-{uuid.uuid4()}",
            run_id=run_id,
            kind="okf-candidate-diff",
            uri=f"okf-candidate://{candidate_id}",
            sha256=hashlib.sha256(git_candidate.diff.encode("utf-8")).hexdigest(),
            metadata_json={
                "candidate_id": candidate_id,
                "base_revision": git_candidate.base_revision,
                "candidate_revision": git_candidate.candidate_revision,
            },
        )
    )
    db.commit()
    return row, git_candidate.diff


def create_import_candidate(
    db: Session,
    active_root: Path | str,
    candidates_root: Path | str,
    actor_id: str | None,
    payload: bytes,
) -> tuple[OKFCandidate, str]:
    candidate_id = f"candidate-{uuid.uuid4()}"
    repository = GitKnowledgeRepository(active_root)
    destination = Path(candidates_root).resolve() / candidate_id

    def build(worktree: Path) -> None:
        for concept_path in worktree.rglob("*.md"):
            concept_path.unlink()
        bundle = FileSystemOKFBundle.import_zip(payload, worktree)
        if not bundle.validate().valid:
            raise ValueError("Imported OKF candidate is not conformant")

    git_candidate = repository.create_candidate(candidate_id, destination, build)
    report = FileSystemOKFBundle(destination).validate()
    row = OKFCandidate(
        id=candidate_id,
        status="pending",
        base_revision=git_candidate.base_revision,
        candidate_revision=git_candidate.candidate_revision,
        worktree_path=str(destination),
        validation_report=report.model_dump(mode="json"),
        created_by=actor_id,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(row)
    db.add(
        Artifact(
            id=f"artifact-{uuid.uuid4()}",
            kind="okf-import-candidate-diff",
            uri=f"okf-candidate://{candidate_id}",
            sha256=hashlib.sha256(git_candidate.diff.encode("utf-8")).hexdigest(),
            metadata_json={
                "candidate_id": candidate_id,
                "base_revision": git_candidate.base_revision,
                "candidate_revision": git_candidate.candidate_revision,
            },
        )
    )
    db.commit()
    return row, git_candidate.diff


async def request_qmd_reindex(qmd_url: str | None) -> str:
    if not qmd_url:
        return "disabled; lexical fallback active"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(qmd_url.rstrip("/") + "/reindex")
            response.raise_for_status()
        return "refreshed"
    except httpx.HTTPError:
        return "unavailable; lexical fallback active"


def approve_candidate(
    db: Session,
    active_root: Path | str,
    candidate_id: str,
    actor_id: str | None,
    reason: str,
) -> tuple[OKFCandidate, str]:
    row = db.get(OKFCandidate, candidate_id)
    if row is None:
        raise LookupError("OKF candidate not found")
    if row.status != "pending" or not row.candidate_revision:
        raise ValueError("OKF candidate is no longer pending")
    now = datetime.now(UTC)
    expires_at = row.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= now:
        row.status = "expired"
        row.decided_at = now
        db.commit()
        raise ValueError("OKF candidate has expired")
    revision = GitKnowledgeRepository(active_root).merge_candidate(
        row.base_revision, row.candidate_revision
    )
    row.status = "approved"
    row.decided_by = actor_id
    row.decision_reason = reason
    row.decided_at = datetime.now(UTC)
    db.commit()
    return row, revision


def reject_candidate(
    db: Session,
    candidate_id: str,
    actor_id: str | None,
    reason: str,
) -> OKFCandidate:
    row = db.get(OKFCandidate, candidate_id)
    if row is None:
        raise LookupError("OKF candidate not found")
    if row.status != "pending":
        raise ValueError("OKF candidate is no longer pending")
    row.status = "rejected"
    row.decided_by = actor_id
    row.decision_reason = reason
    row.decided_at = datetime.now(UTC)
    db.commit()
    return row
