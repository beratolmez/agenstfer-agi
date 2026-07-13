import hashlib
import json
from pathlib import Path

from agi_server.connectors.files import ReadOnlyTabularConnector
from agi_server.db import (
    Base,
    CanonicalEntity,
    CanonicalFact,
    DataSource,
    EvidenceItem,
    RawSnapshotRow,
    SourceMapping,
    SourceSyncRun,
)
from agi_server.domain.diagnostic import build_growth_diagnostic
from agi_server.ingestion.service import (
    resolve_evidence_excerpt,
    sync_connector,
    sync_demo_company,
)
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker


def test_demo_sync_persists_sources_snapshots_entities_and_real_evidence(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite:///{(tmp_path / 'ingestion.db').as_posix()}")
    Base.metadata.create_all(engine)
    local_session = sessionmaker(bind=engine, expire_on_commit=False)
    raw_root = tmp_path / "raw"

    with local_session() as db:
        summary = sync_demo_company(db, raw_root)
        assert summary.total_records == 1783
        assert {item.source_id for item in summary.sources} == {
            "src-crm-001",
            "src-erp-001",
            "src-strategy-001",
        }
        assert db.scalar(select(func.count()).select_from(DataSource)) == 3
        assert db.scalar(select(func.count()).select_from(SourceMapping)) == 3
        assert db.scalar(select(func.count()).select_from(SourceSyncRun)) == 3
        assert db.scalar(select(func.count()).select_from(RawSnapshotRow)) == 3
        assert db.scalar(select(func.count()).select_from(CanonicalEntity)) == 1783
        assert db.scalar(select(func.count()).select_from(CanonicalFact)) > 5000
        assert db.scalar(select(func.count()).select_from(EvidenceItem)) == 1783

        diagnostic = build_growth_diagnostic(db)
        reference = diagnostic.opportunities[0].evidence[0]
        assert (
            reference.snapshot_sha256
            != hashlib.sha256(
                f"{reference.source_id}:accounts:18:{reference.label}".encode()
            ).hexdigest()
        )
        resolved = resolve_evidence_excerpt(db, raw_root, reference.id)
        assert resolved is not None
        assert resolved["locator"]["sheet"] == "accounts"
        assert resolved["excerpt"]["id"] == "acc-017"

        snapshot = db.get(RawSnapshotRow, resolved["snapshot_id"])
        assert snapshot is not None
        payload = json.loads((raw_root / snapshot.file_path).read_text(encoding="utf-8"))
        assert payload["format"] == "agi-raw-records-v1"

        second = sync_demo_company(db, raw_root)
        assert second.total_records == 1783
        assert db.scalar(select(func.count()).select_from(RawSnapshotRow)) == 3
        assert db.scalar(select(func.count()).select_from(EvidenceItem)) == 1783

    engine.dispose()


def test_mapped_csv_uses_same_snapshot_and_evidence_pipeline(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite:///{(tmp_path / 'file.db').as_posix()}")
    Base.metadata.create_all(engine)
    local_session = sessionmaker(bind=engine, expire_on_commit=False)
    source_path = tmp_path / "accounts.csv"
    source_path.write_text(
        "Account ID,Customer Name,Note\nacc-1,Atlas,=HYPERLINK(test)\n",
        encoding="utf-8",
    )

    with local_session() as db:
        db.add(
            DataSource(
                id="src-file-1",
                name="accounts.csv",
                connector_type="tabular-file",
                configuration={"classification": "confidential"},
                read_only=True,
                status="mapped",
            )
        )
        db.commit()
        connector = ReadOnlyTabularConnector(
            source_path,
            "src-file-1",
            "accounts",
            field_mapping={"id": "Account ID", "name": "Customer Name", "note": "Note"},
        )
        _, warnings = connector.preview_with_warnings()
        assert warnings

        summary = sync_connector(db, connector, tmp_path / "raw")
        assert summary.total_records == 1
        entity = db.scalar(select(CanonicalEntity))
        evidence = db.scalar(select(EvidenceItem))
        assert entity is not None and entity.attributes["name"] == "Atlas"
        assert entity.classification == "confidential"
        assert evidence is not None and evidence.classification == "confidential"
        resolved = resolve_evidence_excerpt(db, tmp_path / "raw", evidence.id)
        assert resolved is not None and resolved["excerpt"]["id"] == "acc-1"

    engine.dispose()
