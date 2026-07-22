"""
End-to-End Simulation Script for "Anka Endüstriyel Otomasyon A.Ş."
Executes steps 1 to 6 and records detailed execution logs.
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime, UTC

# Insert python paths
sys.path.insert(0, os.path.abspath("apps/api"))
sys.path.insert(0, os.path.abspath("apps/services/ai-agent"))
sys.path.insert(0, os.path.abspath("apps/services/rag"))

from unittest.mock import MagicMock
mock_rag = MagicMock()
mock_rag.retrieve.retrieve_knowledge.return_value = {
    "documents": [["Mock doc"]],
    "metadatas": [[{"source": "mock.md"}]],
    "distances": [[0.5]],
}
sys.modules.setdefault("rag_service", mock_rag)
sys.modules.setdefault("rag_service.retrieve", mock_rag.retrieve)
sys.modules.setdefault("rag_service.ingest", mock_rag.ingest)

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from agi_server.db import (
    Base,
    WorkflowDefinitionRow,
    WorkflowRun,
    WorkflowStepRun,
    OKFCandidate,
    ApprovalRequest,
    EvidenceItem,
    CanonicalEntity,
)
from agi_server.config import Settings
from agi_server.ingestion import sync_demo_company
from agi_server.okf.lifecycle import ensure_active_repository
from agi_server.workflow.triggers import trigger_engine
from agi_server.workflow import build_default_workflow
from agi_server.workflow.registry_service import ensure_platform_registry
from agi_server.workflow.persistent_runtime import (
    start_persisted_workflow,
    decide_persisted_approval,
)
from agi_server.domain.metrics import calculate_verified_growth_metrics
from agi_server.agents.contracts import (
    CompanyAnalysis,
    OpportunityHypotheses,
    OpportunityHypothesis,
    MaterialClaim,
    EvidenceReview,
    EvidenceDecision,
    OKFChangeSet,
)
from agi_server.diagnostics.service import _material_claims
from agi_server.okf.git_repo import GitKnowledgeRepository

from ai_agent.graph import create_graph


def run_simulation(tmp_dir: Path):
    logs = []

    def log(msg: str):
        timestamp = datetime.now(UTC).isoformat()
        entry = f"[{timestamp}] {msg}"
        print(entry)
        logs.append(entry)

    log("=== STARTING END-TO-END WORKFLOW SIMULATION FOR ANKA ENDÜSTRİYEL OTOMASYON A.Ş. ===")

    # Setup DB
    db_path = tmp_dir / "sim.db"
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    # 1. Simulate webhook event
    log("Step 1: Simulating Webhook Event POST /api/webhooks/src-crm-001...")
    payload = {
        "company_name": "Anka Endüstriyel Otomasyon A.Ş.",
        "contact_email": "satinalma@anka-otomasyon.com.tr",
        "intent_score": 92,
        "location": "Kocaeli / Bursa",
    }
    event_type = "inbound.form_submitted"
    evt = trigger_engine.record_event(
        source_id="src-crm-001",
        event_type=event_type,
        payload=payload,
        status="triggered",
    )
    log(f"Webhook event recorded: Event ID={evt['id']}, Source={evt['source_id']}, Status={evt['status']}")

    # 2. Verify trigger rule matching
    log("Step 2: Matching Trigger Rules...")
    matched_rules = trigger_engine.match_rules(event_type)
    for rule in matched_rules:
        log(f"Matched Rule: ID={rule.id}, Name={rule.name}, Target Workflow={rule.target_workflow_id}")
    assert len(matched_rules) > 0, "No trigger rules matched!"

    # 3. StateGraph execution across 7 KDS AI ABS Agent Nodes
    log("Step 3: Compiling and invoking StateGraph across 7 KDS AI ABS specialized agent nodes...")
    graph = create_graph()
    graph_result = graph.invoke({
        "messages": ["Run full KDS AI ABS diagnostic for Anka Endüstriyel Otomasyon A.Ş."],
        "company_name": "Anka Endüstriyel Otomasyon A.Ş.",
    })
    kds_nodes = [
        ("CompanyAnalysis", "company_profiling_data"),
        ("LeadOpportunity", "lead_opportunity_data"),
        ("CompetitorIntelligence", "competitor_intelligence_data"),
        ("SecurityAudit", "security_audit_data"),
        ("FinancialDiagnostics", "financial_diagnostics_data"),
        ("SEOBrandIntelligence", "seo_brand_intelligence_data"),
        ("CustomerSatisfaction", "customer_satisfaction_data"),
    ]
    for agent_contract, key in kds_nodes:
        has_output = key in graph_result and graph_result[key] is not None
        log(f"KDS Node [{agent_contract}] execution output key '{key}': {'PRESENT' if has_output else 'MISSING'}")
        assert has_output, f"Missing output for {agent_contract}"

    # 4. Ingest data and confirm evidence grounding locators (ev_...) linked in DB
    log("Step 4: Syncing company raw data and verifying evidence locators (ev_...)...")
    knowledge_root = tmp_dir / "knowledge"
    settings = Settings(
        database_url=f"sqlite:///{db_path.as_posix()}",
        knowledge_root=knowledge_root,
        model_profile="local-balanced",
    )
    with Session() as db:
        sync_summary = sync_demo_company(db, settings.raw_root)
        log(f"Demo company data synced: Total Records={sync_summary.total_records}")

        evidence_count = db.query(EvidenceItem).count()
        sample_evidences = db.scalars(select(EvidenceItem.id).limit(5)).all()
        log(f"Persisted EvidenceItem count={evidence_count}. Sample evidence IDs: {sample_evidences}")
        assert evidence_count > 0

        ensure_active_repository(settings.company_bundle)
        ensure_platform_registry(db)

        # 5. Run persistent workflow execution & confirm human approval candidate generated
        log("Step 5: Executing persistent workflow and generating human approval candidate...")
        default_wf = build_default_workflow()
        wf_row = db.get(WorkflowDefinitionRow, (default_wf.id, default_wf.version))

        # Mock structured model outputs for workflow test model
        metrics = calculate_verified_growth_metrics(db)
        first_ev = metrics.signals[0].evidence_ids[0]
        company = CompanyAnalysis(
            summary="Anka Endüstriyel Otomasyon A.Ş. maintains strong customer traction in Turkey.",
            segments=["Industrial Automation"],
            strengths=[MaterialClaim(id="str-1", text="Anka-PLC-5000 is installed.", evidence_ids=[first_ev])],
            weaknesses=[MaterialClaim(id="wk-1", text="Needs support optimization.", evidence_ids=[first_ev])],
            data_gaps=["Consent metadata"],
        )
        hypotheses = OpportunityHypotheses(
            hypotheses=[
                OpportunityHypothesis(
                    signal_id=sig.id,
                    title=f"Opportunity: {sig.title}",
                    rationale="Grounding confirmed via raw evidence.",
                    evidence_ids=[sig.evidence_ids[0]],
                )
                for sig in metrics.signals
            ]
        )
        claims = _material_claims(metrics, company, hypotheses)
        review = EvidenceReview(
            approved=True,
            decisions=[
                EvidenceDecision(
                    claim_id=c.id,
                    supported=True,
                    evidence_ids=[c.evidence_ids[0]],
                    reason="Grounding verified.",
                )
                for c in claims
            ],
            contradictions=[],
        )
        change_set = OKFChangeSet(
            summary="Anka Growth Diagnostic OKF candidate patch.",
            concept_paths=["reports/growth-diagnostic.md"],
            source_ids=["src-crm-001", "src-erp-001"],
        )

        from pydantic_ai.models.test import TestModel
        model_overrides = {
            "company-analyst": TestModel(call_tools=[], custom_output_args=company.model_dump(mode="json")),
            "growth-opportunity-analyst": TestModel(call_tools=[], custom_output_args=hypotheses.model_dump(mode="json")),
            "evidence-reviewer": TestModel(call_tools=[], custom_output_args=review.model_dump(mode="json")),
            "wiki-curator": TestModel(call_tools=[], custom_output_args=change_set.model_dump(mode="json")),
        }

        run = asyncio.run(
            start_persisted_workflow(
                db,
                settings,
                wf_row,
                idempotency_key="sim-anka-run-001",
                actor_id="admin-sim",
                model_overrides=model_overrides,
            )
        )
        log(f"WorkflowRun created: ID={run.id}, Status={run.status}, Artifact={run.artifact_uri}")

        candidate = db.scalar(select(OKFCandidate).where(OKFCandidate.run_id == run.id))
        approval = db.scalar(select(ApprovalRequest).where(ApprovalRequest.run_id == run.id))
        log(f"OKFCandidate created: ID={candidate.id}, Status={candidate.status}")
        log(f"ApprovalRequest created: ID={approval.id}, Status={approval.status}")
        assert candidate is not None and approval is not None

        # 6. Verify approval decision recording & OKF wiki patch proposal
        log("Step 6: Recording human approval decision and proposing OKF wiki patch...")
        before_git = GitKnowledgeRepository(settings.company_bundle).ensure_baseline()

        resumed_run, qmd_res = asyncio.run(
            decide_persisted_approval(
                db,
                settings,
                approval,
                decision="approved",
                reason="Approved by human reviewer for Anka Endüstriyel Otomasyon A.Ş.",
                actor_id="reviewer-admin",
                idempotency_key="sim-decide-001",
            )
        )
        after_git = GitKnowledgeRepository(settings.company_bundle).ensure_baseline()

        log(f"Approval decision executed: Resumed Workflow Status={resumed_run.status}")
        log(f"Updated Candidate Status={candidate.status}, Approval Status={approval.status}")
        log(f"OKF Wiki Patch committed. Git Baseline before={before_git[:8]}, after={after_git[:8]}")

        log("=== SIMULATION COMPLETED SUCCESSFULLY ===")

    engine.dispose()
    return logs

if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        run_simulation(Path(tmpdir))
