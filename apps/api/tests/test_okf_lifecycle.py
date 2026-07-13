from pathlib import Path

from agi_server.db import Base, OKFCandidate
from agi_server.ingestion.service import sync_demo_company
from agi_server.okf.bundle import FileSystemOKFBundle
from agi_server.okf.lifecycle import (
    approve_candidate,
    create_demo_candidate,
    create_import_candidate,
    ensure_active_repository,
    reject_candidate,
)
from agi_server.okf.models import OKFConcept
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_candidate_rejection_cannot_change_active_and_approval_fast_forwards(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'candidate.db').as_posix()}")
    Base.metadata.create_all(engine)
    local_session = sessionmaker(bind=engine, expire_on_commit=False)
    active = tmp_path / "knowledge" / "bundles" / "company"
    candidates = tmp_path / "knowledge" / "candidates"

    with local_session() as db:
        baseline = ensure_active_repository(active)
        sync_demo_company(db, tmp_path / "knowledge" / "raw")

        rejected, rejected_diff = create_demo_candidate(db, active, candidates, "approver-1")
        assert rejected_diff
        reject_candidate(db, rejected.id, "approver-1", "Evidence requires correction")
        assert not (active / "reports" / "growth-diagnostic-v1.md").exists()
        assert rejected.base_revision == baseline

        pending, pending_diff = create_demo_candidate(db, active, candidates, "approver-1")
        assert "snapshot_sha256" in pending_diff
        approved, revision = approve_candidate(
            db,
            active,
            pending.id,
            "approver-1",
            "Evidence chain reviewed and accepted",
        )
        assert approved.status == "approved"
        assert revision == approved.candidate_revision
        assert (active / "reports" / "growth-diagnostic-v1.md").is_file()
        reference = FileSystemOKFBundle(active).read("references/src-crm-001.md")
        assert reference.frontmatter["agi"]["snapshot_sha256"] != "demo-fixture-hash"
        assert db.get(OKFCandidate, rejected.id).status == "rejected"

        portable = FileSystemOKFBundle(tmp_path / "portable")
        portable.create("Portable")
        portable.write(
            OKFConcept(
                path="custom/vendor-concept.md",
                frontmatter={
                    "type": "VendorExtension",
                    "title": "Vendor concept",
                    "description": "Round-trip extension",
                    "timestamp": "2026-07-13T12:00:00Z",
                    "vendor": {"keep": True},
                    "agi": {"sensitivity": "internal"},
                },
                body="# Vendor concept\n",
            )
        )
        imported, import_diff = create_import_candidate(
            db,
            active,
            candidates,
            "approver-1",
            portable.export_zip(),
        )
        assert "vendor-concept.md" in import_diff
        approve_candidate(
            db,
            active,
            imported.id,
            "approver-1",
            "Portable bundle validation passed",
        )
        loaded = FileSystemOKFBundle(active).read("custom/vendor-concept.md")
        assert loaded.frontmatter["vendor"] == {"keep": True}
        assert not (active / "reports" / "growth-diagnostic-v1.md").exists()

    engine.dispose()
