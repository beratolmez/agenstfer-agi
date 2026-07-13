from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from agi_server.connectors.base import ConnectorPort, RawRecord
from agi_server.connectors.demo import DemoCompanyConnector
from agi_server.db import (
    CanonicalEntity,
    CanonicalFact,
    DataSource,
    EvidenceItem,
    RawSnapshotRow,
    SourceMapping,
    SourceSyncRun,
    utcnow,
)
from agi_server.ingestion.raw_vault import RawVault

SOURCE_NAMES = {
    "src-crm-001": "Anka Sentetik CRM",
    "src-erp-001": "Anka Sentetik ERP",
    "src-strategy-001": "Anka Strateji Dokümanları",
}


class SourceSyncSummary(BaseModel):
    source_id: str
    sync_run_id: str
    snapshot_id: str
    snapshot_sha256: str
    records: int
    status: str


class IngestionSummary(BaseModel):
    sources: list[SourceSyncSummary]
    total_records: int


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256(":".join(parts).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[: min(64, 79 - len(prefix))]}"


def _read_all(connector: ConnectorPort) -> tuple[list[RawRecord], list[str]]:
    records: list[RawRecord] = []
    warnings: list[str] = []
    cursor: str | None = None
    while True:
        page = connector.sync(cursor)
        records.extend(page.records)
        warnings.extend(page.warnings)
        if page.complete:
            return records, warnings
        if not page.next_cursor or page.next_cursor == cursor:
            raise RuntimeError("Connector returned an invalid pagination cursor")
        cursor = page.next_cursor


def _upsert_source(db: Session, source_id: str, records: list[RawRecord]) -> DataSource:
    row = db.get(DataSource, source_id)
    if row is None:
        row = DataSource(
            id=source_id,
            name=SOURCE_NAMES.get(source_id, source_id),
            connector_type="demo",
            configuration={"fixture": "anka", "mode": "read-only"},
            read_only=True,
            status="ready",
        )
        db.add(row)
    else:
        row.name = SOURCE_NAMES.get(source_id, row.name)
        row.status = "ready"
        row.updated_at = utcnow()

    mapping = db.get(SourceMapping, (source_id, 1))
    if mapping is None:
        fields: dict[str, list[str]] = {}
        for record in records:
            fields.setdefault(record.entity_type, sorted(record.data))
        db.add(
            SourceMapping(
                source_id=source_id,
                version=1,
                entity_type="*",
                field_mapping={"entities": fields, "strategy": "identity"},
                validation={"read_only": True, "required": ["id"]},
            )
        )
    return row


def _persist_group(
    db: Session,
    vault: RawVault,
    raw_root: Path,
    source_id: str,
    records: list[RawRecord],
    warnings: list[str],
) -> SourceSyncSummary:
    source = _upsert_source(db, source_id, records)
    classification = str(source.configuration.get("classification", "internal"))
    run = SourceSyncRun(source_id=source_id, status="running", warnings=warnings)
    db.add(run)
    db.flush()

    payload = _canonical_json(
        {
            "format": "agi-raw-records-v1",
            "source_id": source_id,
            "records": [item.model_dump(mode="json") for item in records],
        }
    )
    expected_hash = hashlib.sha256(payload).hexdigest()
    filename = f"{expected_hash}.json"
    snapshot = vault.store(source_id, filename, payload, "demo-company")
    snapshot_id = _stable_id("snap", source_id, snapshot.sha256)
    snapshot_row = db.get(RawSnapshotRow, snapshot_id)
    if snapshot_row is None:
        snapshot_row = RawSnapshotRow(
            id=snapshot_id,
            source_id=source_id,
            filename=filename,
            file_path=str(Path(source_id) / filename),
            sha256=snapshot.sha256,
            bytes=snapshot.bytes,
            source_type=snapshot.source_type,
            classification=classification,
            collected_at=datetime.fromisoformat(snapshot.collected_at.replace("Z", "+00:00")),
        )
        db.add(snapshot_row)

    for record in records:
        entity_id = _stable_id("ent", record.entity_type, record.external_id)
        safe_data = record.model_dump(mode="json")["data"]
        entity = db.get(CanonicalEntity, entity_id)
        external_keys = {source_id: record.external_id}
        if entity is None:
            entity = CanonicalEntity(
                id=entity_id,
                entity_type=record.entity_type,
                external_keys=external_keys,
                attributes=safe_data,
                classification=classification,
            )
            db.add(entity)
        else:
            entity.external_keys = {**entity.external_keys, **external_keys}
            entity.attributes = safe_data
            entity.updated_at = utcnow()

        evidence_id = _stable_id("ev", source_id, record.entity_type, record.external_id)
        evidence = db.get(EvidenceItem, evidence_id)
        locator = {
            **record.locator,
            "entity_type": record.entity_type,
            "external_id": record.external_id,
        }
        excerpt_hash = hashlib.sha256(_canonical_json(safe_data)).hexdigest()
        if evidence is None:
            db.add(
                EvidenceItem(
                    id=evidence_id,
                    source_id=source_id,
                    snapshot_sha256=snapshot.sha256,
                    locator=locator,
                    excerpt_hash=excerpt_hash,
                    classification=classification,
                    raw_snapshot_id=snapshot_id,
                    entity_id=entity_id,
                )
            )
        else:
            evidence.snapshot_sha256 = snapshot.sha256
            evidence.locator = locator
            evidence.excerpt_hash = excerpt_hash
            evidence.raw_snapshot_id = snapshot_id
            evidence.entity_id = entity_id

        relations = {"account_id": "accounts", "product_id": "products"}
        for predicate, raw_value in safe_data.items():
            if predicate == "id":
                continue
            fact_id = _stable_id("fact", entity_id, predicate)
            fact = db.get(CanonicalFact, fact_id)
            related_type = relations.get(predicate)
            object_entity_id = (
                _stable_id("ent", related_type, str(raw_value))
                if related_type and raw_value is not None
                else None
            )
            value = None if object_entity_id else {"value": raw_value}
            if fact is None:
                db.add(
                    CanonicalFact(
                        id=fact_id,
                        subject_id=entity_id,
                        predicate=predicate,
                        object_entity_id=object_entity_id,
                        value=value,
                        evidence_ids=[evidence_id],
                    )
                )
            else:
                fact.object_entity_id = object_entity_id
                fact.value = value
                fact.evidence_ids = [evidence_id]

    run.records_seen = len(records)
    run.records_persisted = len(records)
    run.status = "completed"
    run.completed_at = utcnow()
    return SourceSyncSummary(
        source_id=source_id,
        sync_run_id=run.id,
        snapshot_id=snapshot_id,
        snapshot_sha256=snapshot.sha256,
        records=len(records),
        status=run.status,
    )


def sync_connector(
    db: Session,
    connector: ConnectorPort,
    raw_root: Path | str,
) -> IngestionSummary:
    health = connector.test_connection()
    if not health.ok:
        raise RuntimeError(health.message)
    records, warnings = _read_all(connector)
    groups: dict[str, list[RawRecord]] = defaultdict(list)
    for record in records:
        groups[record.source_id].append(record)

    resolved_root = Path(raw_root).resolve()
    vault = RawVault(resolved_root)
    summaries = [
        _persist_group(db, vault, resolved_root, source_id, group, warnings)
        for source_id, group in sorted(groups.items())
    ]
    db.commit()
    return IngestionSummary(
        sources=summaries,
        total_records=sum(item.records for item in summaries),
    )


def sync_demo_company(db: Session, raw_root: Path | str) -> IngestionSummary:
    return sync_connector(db, DemoCompanyConnector(), raw_root)


def resolve_evidence_excerpt(
    db: Session,
    raw_root: Path | str,
    evidence_id: str,
) -> dict[str, Any] | None:
    evidence = db.get(EvidenceItem, evidence_id)
    if evidence is None or not evidence.raw_snapshot_id:
        return None
    snapshot = db.get(RawSnapshotRow, evidence.raw_snapshot_id)
    if snapshot is None:
        return None
    path = (Path(raw_root).resolve() / snapshot.file_path).resolve()
    if not path.is_relative_to(Path(raw_root).resolve()) or not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    for record in payload.get("records", []):
        if record.get("entity_type") == evidence.locator.get("entity_type") and record.get(
            "external_id"
        ) == evidence.locator.get("external_id"):
            excerpt = record.get("data", {})
            if hashlib.sha256(_canonical_json(excerpt)).hexdigest() != evidence.excerpt_hash:
                raise RuntimeError("Evidence excerpt hash does not match immutable snapshot")
            return {
                "id": evidence.id,
                "source_id": evidence.source_id,
                "snapshot_id": snapshot.id,
                "snapshot_sha256": snapshot.sha256,
                "classification": evidence.classification,
                "locator": evidence.locator,
                "excerpt": excerpt,
                "collected_at": evidence.collected_at,
            }
    return None


def list_sources(db: Session) -> list[DataSource]:
    return list(db.scalars(select(DataSource).order_by(DataSource.id)))
