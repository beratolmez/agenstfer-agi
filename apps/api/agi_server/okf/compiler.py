from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from agi_server.domain.diagnostic import build_growth_diagnostic
from agi_server.okf.bundle import FileSystemOKFBundle
from agi_server.okf.models import OKFConcept


def _timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def compile_demo_bundle(root: Path | str) -> FileSystemOKFBundle:
    bundle = FileSystemOKFBundle(root)
    bundle.create("Anka Endüstriyel Otomasyon Bilgi Bundle'ı")
    common = {
        "timestamp": _timestamp(),
        "agi": {
            "verification_status": "reviewed",
            "sensitivity": "internal",
            "revision": 1,
        },
    }
    bundle.write(
        OKFConcept(
            path="organization/anka-endustriyel-otomasyon.md",
            frontmatter={
                "type": "Organization",
                "title": "Anka Endüstriyel Otomasyon",
                "description": "Sentetik endüstriyel otomasyon şirketi.",
                "resource": "urn:agi:organization:anka",
                "tags": ["organization", "industrial-b2b", "demo"],
                **common,
            },
            body=(
                "# Anka Endüstriyel Otomasyon\n\n"
                "MVP'nin gerçek adapter sözleşmelerini kullanan sentetik tasarım ortağıdır. "
                "[CRM kaynağına](/references/src-crm-001.md) ve "
                "[ERP kaynağına](/references/src-erp-001.md) bağlıdır.\n\n"
                "# Citations\n\n"
                "1. [Sentetik CRM snapshot](/references/src-crm-001.md)\n"
                "2. [Sentetik ERP snapshot](/references/src-erp-001.md)\n"
            ),
        )
    )
    for source_id, label, source_type in [
        ("src-crm-001", "Sentetik CRM snapshot", "demo-crm"),
        ("src-erp-001", "Sentetik ERP snapshot", "demo-erp"),
        ("src-strategy-001", "90 günlük strateji belgesi", "markdown"),
    ]:
        bundle.write(
            OKFConcept(
                path=f"references/{source_id}.md",
                frontmatter={
                    "type": "Reference",
                    "title": label,
                    "description": f"{label} için immutable kaynak kaydı.",
                    "resource": f"urn:agi:reference:{source_id}",
                    "tags": ["reference", source_type],
                    **common,
                    "agi": {
                        **common["agi"],
                        "source_ids": [source_id],
                        "snapshot_sha256": "demo-fixture-hash",
                        "source_type": source_type,
                    },
                },
                body=f"# {label}\n\nKaynak türü: `{source_type}`. Demo fixture'dan üretilmiştir.\n",
            )
        )
    diagnostic = build_growth_diagnostic()
    citation_lines: list[str] = []
    seen: set[str] = set()
    for opportunity in diagnostic.opportunities:
        for evidence in opportunity.evidence:
            if evidence.source_id not in seen:
                seen.add(evidence.source_id)
                citation_lines.append(
                    f"{len(citation_lines) + 1}. [{evidence.label}]"
                    f"(/references/{evidence.source_id}.md)"
                )
    opportunity_lines = [
        f"{index}. **{item.title}** — {item.score}/100; "
        f"kanıt kapsamı %{item.factors.evidence_coverage:.0f}."
        for index, item in enumerate(diagnostic.opportunities, start=1)
    ]
    bundle.write(
        OKFConcept(
            path="reports/growth-diagnostic-v1.md",
            frontmatter={
                "type": "Growth Diagnostic",
                "title": "Growth Diagnostic v1",
                "description": "Sentetik şirket için kanıta bağlı büyüme tanısı ve 30 günlük plan.",
                "resource": "urn:agi:report:growth-diagnostic-v1",
                "tags": ["growth-diagnostic", "demo", "draft"],
                **common,
                "agi": {
                    **common["agi"],
                    "verification_status": "candidate",
                    "evidence_coverage": diagnostic.evidence_coverage / 100,
                    "source_ids": sorted(seen),
                },
            },
            body=(
                "# Growth Diagnostic v1\n\n"
                f"{diagnostic.summary}\n\n"
                "## Öncelikli fırsatlar\n\n"
                + "\n".join(opportunity_lines)
                + "\n\n## 30 günlük plan\n\n"
                + "\n".join(f"- **Hafta {item.week}:** {item.title}" for item in diagnostic.plan)
                + "\n\n# Citations\n\n"
                + "\n".join(citation_lines)
                + "\n"
            ),
        )
    )
    bundle.generate_index()
    bundle.update_log("Sentetik şirket ve Growth Diagnostic v1 derlendi")
    return bundle
