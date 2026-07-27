from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from agi_server.db import CanonicalEntity, EvidenceItem
from agi_server.schemas import DemoCounts, ScoreFactors


class MetricValue(BaseModel):
    key: str
    value: int | float
    unit: str
    evidence_ids: list[str]


class OpportunitySignal(BaseModel):
    id: str
    title: str
    subtitle: str
    factors: ScoreFactors
    evidence_ids: list[str]
    verification_source_evidence_ids: list[str] = Field(default_factory=list)
    metrics: dict[str, int | float]
    verification_evidence_id: str | None = None


class MetricSnapshot(BaseModel):
    counts: DemoCounts
    metrics: dict[str, MetricValue]
    signals: list[OpportunitySignal]
    data_readiness: int
    evidence_coverage: int
    data_gaps: list[str]
    planted_insights: list[str]


METRIC_CALCULATION_VERSION = "growth-metrics-v1"
_CLASSIFICATION_ORDER = {"public": 0, "internal": 1, "confidential": 2, "restricted": 3}


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def calculate_verified_growth_metrics(db: Session) -> MetricSnapshot:
    """Calculate metrics and bind each aggregate to immutable source evidence."""
    metrics = calculate_growth_metrics(db)
    verified_signals: list[OpportunitySignal] = []
    for signal in metrics.signals:
        source_evidence_ids = sorted(
            set(signal.verification_source_evidence_ids or signal.evidence_ids)
        )
        source_rows = [db.get(EvidenceItem, evidence_id) for evidence_id in source_evidence_ids]
        if any(row is None for row in source_rows):
            raise ValueError(f"Metric signal {signal.id} references missing source evidence")
        rows = [row for row in source_rows if row is not None]
        invalid_classifications = {
            row.classification for row in rows if row.classification not in _CLASSIFICATION_ORDER
        }
        if invalid_classifications:
            raise ValueError(
                "Metric source evidence has invalid classifications: "
                f"{sorted(invalid_classifications)}"
            )
        members = [
            {
                "id": row.id,
                "snapshot_sha256": row.snapshot_sha256,
                "excerpt_hash": row.excerpt_hash,
                "classification": row.classification,
            }
            for row in rows
        ]
        source_digest = hashlib.sha256(_canonical_json(members)).hexdigest()
        receipt = {
            "kind": "deterministic_metric",
            "calculation_version": METRIC_CALCULATION_VERSION,
            "signal_id": signal.id,
            "metrics": signal.metrics,
            "factors": signal.factors.model_dump(mode="json"),
            "score": signal.factors.total(),
            "source_evidence_count": len(members),
            "source_evidence_digest": source_digest,
        }
        receipt_hash = hashlib.sha256(_canonical_json(receipt)).hexdigest()
        evidence_id = f"ev-metric-{signal.id}-{receipt_hash[:12]}"
        classification = max(
            (row.classification for row in rows),
            key=lambda value: _CLASSIFICATION_ORDER.get(value, 3),
            default="internal",
        )
        evidence = db.get(EvidenceItem, evidence_id)
        locator = {
            "kind": "deterministic_metric",
            "receipt": receipt,
            "source_evidence_ids": [row.id for row in rows],
        }
        if evidence is None:
            db.add(
                EvidenceItem(
                    id=evidence_id,
                    source_id="agi:deterministic-metrics",
                    snapshot_sha256=receipt_hash,
                    locator=locator,
                    excerpt_hash=receipt_hash,
                    classification=classification,
                )
            )
        else:
            if evidence.excerpt_hash != receipt_hash or evidence.locator != locator:
                raise RuntimeError("Persisted metric receipt does not match deterministic output")
        verified_signals.append(
            signal.model_copy(update={"verification_evidence_id": evidence_id})
        )
    db.flush()
    return metrics.model_copy(update={"signals": verified_signals})


def _clamp(value: float, minimum: float = 0, maximum: float = 100) -> float:
    return round(max(minimum, min(maximum, value)), 2)


def calculate_growth_metrics(db: Session) -> MetricSnapshot:
    data_gaps: list[str] = []
    entities = list(db.scalars(select(CanonicalEntity)))
    grouped: dict[str, list[CanonicalEntity]] = defaultdict(list)
    for entity in entities:
        grouped[entity.entity_type].append(entity)
    evidence_by_entity: dict[str, list[str]] = defaultdict(list)
    for item in db.scalars(select(EvidenceItem)):
        if item.entity_id is not None:
            evidence_by_entity[item.entity_id].append(item.id)
    for evidence_ids in evidence_by_entity.values():
        evidence_ids.sort()

    def evidence_for(
        rows: list[CanonicalEntity], limit: int | None = 50
    ) -> list[str]:
        result = [
            evidence_id
            for row in rows
            for evidence_id in evidence_by_entity.get(row.id, [])
        ]
        return result if limit is None else result[:limit]

    accounts = grouped["accounts"]
    contacts = grouped["contacts"]
    opportunities = grouped["opportunities"]
    products = grouped["products"]
    transactions = grouped["orders_invoices"]
    activities = grouped["activities"]
    counts = DemoCounts(
        accounts=len(accounts),
        contacts=len(contacts),
        opportunities=len(opportunities),
        products=len(products),
        orders_invoices=len(transactions),
        activities=len(activities),
    )
    if not accounts and not transactions:
        data_gaps.append("Senkronize edilmiş account ve işlem verisi bulunamadı")

    high_energy = [
        row for row in accounts if float(row.attributes.get("energy_intensity", 0)) >= 0.75
    ]
    installed = [row for row in accounts if int(row.attributes.get("installed_base", 0)) >= 5]
    exporters = [row for row in accounts if float(row.attributes.get("export_ratio", 0)) >= 0.55]
    stale = [row for row in accounts if row.attributes.get("lifecycle_status") == "stale"]
    missing_contacts = [row for row in contacts if not row.attributes.get("email")]
    product_names = {
        str(row.attributes.get("id")): str(row.attributes.get("name")) for row in products
    }
    transactions_by_product: dict[str, list[CanonicalEntity]] = defaultdict(list)
    account_purchase_counts: Counter[str] = Counter()
    for row in transactions:
        product_name = product_names.get(str(row.attributes.get("product_id")), "Unknown")
        transactions_by_product[product_name].append(row)
        account_purchase_counts[str(row.attributes.get("account_id"))] += 1
    repeat_accounts = sum(1 for count in account_purchase_counts.values() if count >= 3)

    def _find_matching_transactions(keywords: tuple[str, ...]) -> list[CanonicalEntity]:
        matched: list[CanonicalEntity] = []
        for p_name, tx_list in transactions_by_product.items():
            p_lower = p_name.lower()
            if any(kw in p_lower for kw in keywords):
                matched.extend(tx_list)
        return matched

    energy_transactions = _find_matching_transactions(
        ("energy", "enerji", "power", "metering", "retrofit", "verimlilik")
    )
    maintenance_transactions = _find_matching_transactions(
        ("maintenance", "bakım", "service", "sla", "priority")
    )
    export_transactions = _find_matching_transactions(
        ("export", "ihracat", "oem", "cabinet", "kit")
    )
    parts_transactions = _find_matching_transactions(
        ("parts", "parça", "plc", "modernization", "conversion", "yedek")
    )
    twin_transactions = _find_matching_transactions(
        ("twin", "ikiz", "commissioning", "visual", "dijital")
    )
    proposal_activities = [row for row in activities if row.attributes.get("kind") == "proposal"]

    metrics = {
        "high_energy_accounts": MetricValue(
            key="high_energy_accounts",
            value=len(high_energy),
            unit="accounts",
            evidence_ids=evidence_for(high_energy),
        ),
        "installed_base_accounts": MetricValue(
            key="installed_base_accounts",
            value=len(installed),
            unit="accounts",
            evidence_ids=evidence_for(installed),
        ),
        "export_ready_accounts": MetricValue(
            key="export_ready_accounts",
            value=len(exporters),
            unit="accounts",
            evidence_ids=evidence_for(exporters),
        ),
        "repeat_purchase_accounts": MetricValue(
            key="repeat_purchase_accounts",
            value=repeat_accounts,
            unit="accounts",
            evidence_ids=evidence_for(transactions),
        ),
        "missing_contact_email": MetricValue(
            key="missing_contact_email",
            value=len(missing_contacts),
            unit="contacts",
            evidence_ids=evidence_for(missing_contacts),
        ),
        "stale_accounts": MetricValue(
            key="stale_accounts",
            value=len(stale),
            unit="accounts",
            evidence_ids=evidence_for(stale),
        ),
    }

    def combined(
        *rows: list[CanonicalEntity], limit: int | None = 50
    ) -> list[str]:
        result: list[str] = []
        for group in rows:
            for evidence_id in evidence_for(group, limit=None):
                if evidence_id not in result:
                    result.append(evidence_id)
        return result if limit is None else result[:limit]

    signals = [
        OpportunitySignal(
            id="energy-retrofit",
            title="Enerji verimliliği retrofit paketleri",
            subtitle="Mevcut müşterilere çapraz satış",
            factors=ScoreFactors(
                goal_alignment=96,
                estimated_impact=_clamp(55 + 120 * len(high_energy) / len(accounts)),
                evidence_coverage=100 if high_energy and energy_transactions else 60,
                urgency=_clamp(70 + 100 * len(stale) / len(accounts)),
                feasibility=_clamp(65 + 80 * len(installed) / len(accounts)),
                risk_penalty=3,
            ),
            evidence_ids=combined(high_energy, energy_transactions),
            verification_source_evidence_ids=combined(
                accounts, energy_transactions, limit=None
            ),
            metrics={
                "high_energy_accounts": len(high_energy),
                "energy_orders": len(energy_transactions),
            },
        ),
        OpportunitySignal(
            id="predictive-maintenance",
            title="Predictive bakım hizmeti",
            subtitle="Tekrarlayan servis geliri",
            factors=ScoreFactors(
                goal_alignment=92,
                estimated_impact=_clamp(50 + 100 * len(installed) / len(accounts)),
                evidence_coverage=100 if installed and maintenance_transactions else 55,
                urgency=82,
                feasibility=_clamp(55 + len(maintenance_transactions)),
                risk_penalty=4,
            ),
            evidence_ids=combined(installed, maintenance_transactions),
            verification_source_evidence_ids=combined(
                accounts, maintenance_transactions, limit=None
            ),
            metrics={
                "installed_base_accounts": len(installed),
                "maintenance_orders": len(maintenance_transactions),
            },
        ),
        OpportunitySignal(
            id="oem-export",
            title="OEM ihracat paketleri",
            subtitle="İhracat pazarı genişletme",
            factors=ScoreFactors(
                goal_alignment=84,
                estimated_impact=_clamp(48 + 120 * len(exporters) / len(accounts)),
                evidence_coverage=100 if exporters and export_transactions else 50,
                urgency=74,
                feasibility=_clamp(58 + len(export_transactions)),
                risk_penalty=5,
            ),
            evidence_ids=combined(exporters, export_transactions),
            verification_source_evidence_ids=combined(
                accounts, export_transactions, limit=None
            ),
            metrics={
                "export_ready_accounts": len(exporters),
                "export_kit_orders": len(export_transactions),
            },
        ),
        OpportunitySignal(
            id="spare-parts-subscription",
            title="Yedek parça abonelik modeli",
            subtitle="Tekrarlayan gelir",
            factors=ScoreFactors(
                goal_alignment=76,
                estimated_impact=_clamp(45 + repeat_accounts / 2),
                evidence_coverage=100 if parts_transactions else 45,
                urgency=68,
                feasibility=_clamp(65 + len(parts_transactions)),
                risk_penalty=3,
            ),
            evidence_ids=combined(parts_transactions),
            verification_source_evidence_ids=combined(transactions, limit=None),
            metrics={
                "repeat_purchase_accounts": repeat_accounts,
                "parts_orders": len(parts_transactions),
            },
        ),
        OpportunitySignal(
            id="digital-twin-commissioning",
            title="Dijital ikiz ve komisyonlama hizmeti",
            subtitle="Proje bazlı yüksek marj",
            factors=ScoreFactors(
                goal_alignment=70,
                estimated_impact=_clamp(48 + len(twin_transactions)),
                evidence_coverage=100 if twin_transactions and proposal_activities else 50,
                urgency=61,
                feasibility=_clamp(50 + len(proposal_activities) / 8),
                risk_penalty=5,
            ),
            evidence_ids=combined(twin_transactions, proposal_activities),
            verification_source_evidence_ids=combined(
                twin_transactions, proposal_activities, limit=None
            ),
            metrics={
                "digital_twin_orders": len(twin_transactions),
                "proposal_activities": len(proposal_activities),
            },
        ),
    ]
    signals.sort(key=lambda item: item.factors.total(), reverse=True)
    missing_ratio = len(missing_contacts) / max(1, len(contacts))
    stale_ratio = len(stale) / len(accounts)
    readiness = round(_clamp(100 - missing_ratio * 25 - stale_ratio * 25))
    coverage = round(sum(item.factors.evidence_coverage for item in signals) / len(signals))
    return MetricSnapshot(
        counts=counts,
        metrics=metrics,
        signals=signals,
        data_readiness=readiness,
        evidence_coverage=coverage,
        data_gaps=[
            f"{len(missing_contacts)} contact kaydında e-posta eksik.",
            f"{len(stale)} account stale olarak işaretli.",
        ],
        planted_insights=[
            *(item.id for item in signals),
            "stale-and-missing-contact-data",
        ],
    )
