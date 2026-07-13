from __future__ import annotations

from collections import Counter, defaultdict

from pydantic import BaseModel
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
    metrics: dict[str, int | float]


class MetricSnapshot(BaseModel):
    counts: DemoCounts
    metrics: dict[str, MetricValue]
    signals: list[OpportunitySignal]
    data_readiness: int
    evidence_coverage: int
    data_gaps: list[str]
    planted_insights: list[str]


def _clamp(value: float, minimum: float = 0, maximum: float = 100) -> float:
    return round(max(minimum, min(maximum, value)), 2)


def calculate_growth_metrics(db: Session) -> MetricSnapshot:
    entities = list(db.scalars(select(CanonicalEntity)))
    grouped: dict[str, list[CanonicalEntity]] = defaultdict(list)
    for entity in entities:
        grouped[entity.entity_type].append(entity)
    evidence_by_entity = {
        item.entity_id: item.id
        for item in db.scalars(select(EvidenceItem))
        if item.entity_id is not None
    }

    def evidence_for(rows: list[CanonicalEntity], limit: int = 50) -> list[str]:
        return [evidence_by_entity[row.id] for row in rows if row.id in evidence_by_entity][:limit]

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
    if not accounts or not transactions:
        raise ValueError("Growth metrics require synchronized account and transaction data")

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

    energy_transactions = transactions_by_product["Enerji İzleme"]
    maintenance_transactions = transactions_by_product["Bakım Paketi"]
    export_transactions = transactions_by_product["OEM Export Kit"]
    parts_transactions = transactions_by_product["Yedek Parça"]
    twin_transactions = transactions_by_product["Dijital İkiz"]
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

    def combined(*rows: list[CanonicalEntity]) -> list[str]:
        result: list[str] = []
        for group in rows:
            for evidence_id in evidence_for(group):
                if evidence_id not in result:
                    result.append(evidence_id)
        return result[:50]

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
