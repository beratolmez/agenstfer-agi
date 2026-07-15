from __future__ import annotations

from sqlalchemy.orm import Session

from agi_server.agents.contracts import CompanyAnalysis, OpportunityHypotheses
from agi_server.db import EvidenceItem
from agi_server.domain.demo import DEMO_COMPANY
from agi_server.domain.metrics import MetricSnapshot
from agi_server.schemas import (
    EvidenceRef,
    GrowthDiagnostic,
    OpportunityRecommendation,
    PlanItem,
)


def build_computed_diagnostic(
    db: Session,
    run_id: str,
    metrics: MetricSnapshot,
    company: CompanyAnalysis,
    hypotheses: OpportunityHypotheses,
) -> GrowthDiagnostic:
    hypothesis_by_signal = {item.signal_id: item for item in hypotheses.hypotheses}
    recommendations: list[OpportunityRecommendation] = []
    for index, signal in enumerate(metrics.signals):
        hypothesis = hypothesis_by_signal[signal.id]
        evidence: list[EvidenceRef] = []
        requested_ids = list(
            dict.fromkeys(
                [
                    *(
                        [signal.verification_evidence_id]
                        if signal.verification_evidence_id
                        else []
                    ),
                    *(hypothesis.evidence_ids or signal.evidence_ids),
                ]
            )
        )
        for evidence_id in requested_ids[:3]:
            row = db.get(EvidenceItem, evidence_id)
            if row is None:
                continue
            evidence.append(
                EvidenceRef(
                    id=row.id,
                    source_id=row.source_id,
                    label=f"{signal.title} kanıtı",
                    locator=row.locator,
                    snapshot_sha256=row.snapshot_sha256,
                    coverage=signal.factors.evidence_coverage / 100,
                )
            )
        if not evidence:
            raise ValueError(f"Signal {signal.id} has no resolvable evidence")
        alignment = (
            "Yüksek"
            if signal.factors.goal_alignment >= 90
            else "Orta-Yüksek"
            if signal.factors.goal_alignment >= 80
            else "Orta"
        )
        recommendations.append(
            OpportunityRecommendation(
                id=signal.id,
                title=hypothesis.title,
                subtitle=signal.subtitle,
                target_alignment=alignment,
                impact=round(signal.factors.estimated_impact / 10, 1),
                factors=signal.factors,
                score=signal.factors.total(),
                status="İncelendi" if index == 0 else "Onay bekliyor" if index == 1 else "Taslak",
                evidence=evidence,
                rationale=hypothesis.rationale,
            )
        )
    recommendations.sort(key=lambda item: item.score, reverse=True)
    return GrowthDiagnostic(
        id=run_id,
        company=DEMO_COMPANY,
        objective="90 gün içinde mevcut müşteri tabanından kârlı büyüme",
        data_readiness=metrics.data_readiness,
        evidence_coverage=metrics.evidence_coverage,
        open_approvals=1,
        summary=company.summary,
        counts=metrics.counts,
        opportunities=recommendations,
        plan=[
            PlanItem(
                week=1,
                range="Gün 1–7",
                title="Kanıt ve account doğrulaması",
                actions=[
                    "İlk 20 account kaydını doğrula",
                    "Fırsat sahiplerini ata",
                    "Eksik contact alanlarını tamamla",
                ],
            ),
            PlanItem(
                week=2,
                range="Gün 8–14",
                title="İş vakası ve müşteri doğrulaması",
                actions=[
                    "Beş müşteri görüşmesi yap",
                    "Deterministic etki hesabını gözden geçir",
                    "Pilot kapsamını onaya hazırla",
                ],
            ),
            PlanItem(
                week=3,
                range="Gün 15–30",
                title="Read-only pilot",
                actions=[
                    "Pilot ölçümünü başlat",
                    "Evidence kapsamını haftalık kontrol et",
                    "Sonuçları Approval Center'a sun",
                ],
            ),
        ],
        data_gaps=[*metrics.data_gaps, *company.data_gaps],
        detected_planted_insights=metrics.planted_insights,
    )
