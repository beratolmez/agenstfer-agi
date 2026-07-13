from __future__ import annotations

from hashlib import sha256

from agi_server.domain.demo import DEMO_COMPANY, build_demo_dataset, demo_counts
from agi_server.schemas import (
    EvidenceRef,
    GrowthDiagnostic,
    OpportunityRecommendation,
    PlanItem,
    ScoreFactors,
)


def _evidence(
    evidence_id: str, source_id: str, label: str, row: int, coverage: float
) -> EvidenceRef:
    digest = sha256(f"{source_id}:{row}:{label}".encode()).hexdigest()
    return EvidenceRef(
        id=evidence_id,
        source_id=source_id,
        label=label,
        locator={"kind": "tabular", "sheet": "records", "row": row, "column": "*"},
        snapshot_sha256=digest,
        coverage=coverage,
    )


def _opportunity(
    *,
    key: str,
    title: str,
    subtitle: str,
    alignment: str,
    impact: float,
    inputs: tuple[float, float, float, float, float, float],
    evidence: list[EvidenceRef],
    rationale: str,
    status: str,
) -> OpportunityRecommendation:
    factors = ScoreFactors(
        goal_alignment=inputs[0],
        estimated_impact=inputs[1],
        evidence_coverage=inputs[2],
        urgency=inputs[3],
        feasibility=inputs[4],
        risk_penalty=inputs[5],
    )
    return OpportunityRecommendation(
        id=key,
        title=title,
        subtitle=subtitle,
        target_alignment=alignment,  # type: ignore[arg-type]
        impact=impact,
        factors=factors,
        score=factors.total(),
        evidence=evidence,
        rationale=rationale,
        status=status,  # type: ignore[arg-type]
    )


def build_growth_diagnostic() -> GrowthDiagnostic:
    dataset = build_demo_dataset()
    crm = "src-crm-001"
    erp = "src-erp-001"
    strategy = "src-strategy-001"
    opportunities = [
        _opportunity(
            key="energy-retrofit",
            title="Enerji verimliliği retrofit paketleri",
            subtitle="Mevcut müşterilere çapraz satış",
            alignment="Yüksek",
            impact=9.1,
            inputs=(96, 94, 82, 88, 84, 3),
            evidence=[
                _evidence(
                    "ev-energy-accounts", crm, "Yüksek enerji yoğunluklu account kümesi", 18, 0.86
                ),
                _evidence("ev-energy-orders", erp, "Enerji izleme kurulu tabanı", 44, 0.78),
            ],
            rationale=(
                "Kurulu tabanı bulunan enerji yoğun müşteriler, düşük entegrasyon "
                "eforuyla çapraz satışa uygundur."
            ),
            status="İncelendi",
        ),
        _opportunity(
            key="predictive-maintenance",
            title="Predictive bakım yazılımı (SaaS)",
            subtitle="Yeni gelir akışı",
            alignment="Yüksek",
            impact=8.6,
            inputs=(92, 88, 74, 84, 78, 4),
            evidence=[
                _evidence("ev-maint-installed", crm, "Sensörlü kurulu taban", 37, 0.74),
                _evidence("ev-maint-service", erp, "Tekrarlayan bakım siparişleri", 102, 0.74),
            ],
            rationale=(
                "Bakım hizmeti alan account'larda sensör verisini abonelik ürününe "
                "dönüştürme zemini vardır."
            ),
            status="Onay bekliyor",
        ),
        _opportunity(
            key="oem-export",
            title="OEM ihracat paketleri",
            subtitle="İhracat pazarı genişletme",
            alignment="Orta-Yüksek",
            impact=8.0,
            inputs=(82, 86, 68, 75, 72, 5),
            evidence=[
                _evidence("ev-export-segment", crm, "Yüksek ihracat oranlı OEM segmenti", 61, 0.68),
                _evidence("ev-export-kit", erp, "OEM Export Kit sipariş geçmişi", 130, 0.68),
            ],
            rationale=(
                "İhracat yoğun müşterilerde standardize edilmiş devreye alma ve "
                "yedek kit paketi satış çevrimini kısaltabilir."
            ),
            status="Taslak",
        ),
        _opportunity(
            key="spare-parts-subscription",
            title="Yedek parça abonelik modeli",
            subtitle="Tekrarlayan gelir",
            alignment="Orta",
            impact=6.8,
            inputs=(72, 70, 64, 68, 82, 3),
            evidence=[
                _evidence("ev-parts-repeat", erp, "Tekrarlayan yedek parça alımları", 211, 0.64)
            ],
            rationale=(
                "Düzenli yedek parça alan account'lar için tüketim tabanlı "
                "replenishment pilotu kurulabilir."
            ),
            status="Taslak",
        ),
        _opportunity(
            key="digital-twin-commissioning",
            title="Dijital ikiz ve komisyonlama hizmeti",
            subtitle="Proje bazlı yüksek marj",
            alignment="Orta",
            impact=6.4,
            inputs=(68, 74, 58, 61, 66, 5),
            evidence=[
                _evidence(
                    "ev-digital-projects",
                    crm,
                    "Devreye alma aktivitesi bulunan projeler",
                    319,
                    0.58,
                ),
                _evidence("ev-strategy", strategy, "90 günlük servis geliri hedefi", 12, 0.58),
            ],
            rationale=(
                "Devreye alma yoğun projelerde simülasyon hizmeti yeni yüksek "
                "marjlı paket olabilir; kanıt kapsamı geliştirilmelidir."
            ),
            status="Taslak",
        ),
    ]
    opportunities.sort(key=lambda item: item.score, reverse=True)
    return GrowthDiagnostic(
        company=DEMO_COMPANY,
        objective="90 gün içinde mevcut müşteri tabanından kârlı büyüme",
        data_readiness=89,
        evidence_coverage=76,
        open_approvals=3,
        summary=(
            "En yüksek etki–düşük çaba fırsatları enerji verimliliği retrofit, "
            "predictive bakım ve OEM ihracat paketlerinde toplanıyor."
        ),
        counts=demo_counts(dataset),
        opportunities=opportunities,
        plan=[
            PlanItem(
                week=1,
                range="Gün 1–7",
                title="Keşif ve önceliklendirme",
                actions=[
                    "Account verisini doğrula",
                    "İlk 20 account brief'ini oluştur",
                    "Fırsat sahiplerini ata",
                ],
            ),
            PlanItem(
                week=2,
                range="Gün 8–14",
                title="Doğrulama ve iş vakası",
                actions=[
                    "Beş müşteri görüşmesi yap",
                    "Finansal etkiyi modelle",
                    "Pilot kapsamını gözden geçir",
                ],
            ),
            PlanItem(
                week=3,
                range="Gün 15–30",
                title="Pilot ve onay",
                actions=[
                    "Pilot kapsamını netleştir",
                    "Read-only ölçümü başlat",
                    "Sonuçları onaya sun",
                ],
            ),
        ],
        data_gaps=[
            "Dokuz contact kaydında e-posta eksik.",
            "Dokuz account 180 günden uzun süredir güncellenmemiş.",
            "Dijital ikiz önerisinin müşteri görüşmesi kanıtı zayıf.",
        ],
        detected_planted_insights=[
            "energy-retrofit",
            "predictive-maintenance",
            "oem-export",
            "spare-parts-subscription",
            "digital-twin-commissioning",
            "stale-and-missing-contact-data",
        ],
    )
