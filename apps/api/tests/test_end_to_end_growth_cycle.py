import asyncio
import json
from pathlib import Path
from unittest.mock import MagicMock
import sys

# Mock optional dependencies before importing agent modules if needed
mock_rag = MagicMock()
mock_rag.retrieve.retrieve_knowledge.return_value = {
    "documents": [["Mock doc"]],
    "metadatas": [[{"source": "mock.md"}]],
    "distances": [[0.5]],
}
sys.modules.setdefault("rag_service", mock_rag)
sys.modules.setdefault("rag_service.retrieve", mock_rag.retrieve)
sys.modules.setdefault("rag_service.ingest", mock_rag.ingest)

import pytest
from fastapi.testclient import TestClient
from pydantic_ai.models.test import TestModel
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from agi_server.agents.contracts import (
    CompanyAnalysis,
    EvidenceDecision,
    EvidenceReview,
    MaterialClaim,
    OKFChangeSet,
    OpportunityHypotheses,
    OpportunityHypothesis,
)
from agi_server.config import Settings
from agi_server.db import (
    ApprovalRequest,
    Base,
    CanonicalEntity,
    EvidenceItem,
    OKFCandidate,
    WorkflowDefinitionRow,
    WorkflowRun,
    WorkflowStepRun,
)
from agi_server.diagnostics.service import _enforce_evidence_gate, _material_claims
from agi_server.domain.metrics import calculate_verified_growth_metrics
from agi_server.ingestion import sync_demo_company
from agi_server.main import app, get_db, get_settings
from agi_server.okf.git_repo import GitKnowledgeRepository
from agi_server.okf.lifecycle import approve_candidate, ensure_active_repository
from agi_server.workflow import build_default_workflow
from agi_server.workflow.persistent_runtime import (
    decide_persisted_approval,
    start_persisted_workflow,
)
from agi_server.workflow.registry_service import ensure_platform_registry
from agi_server.workflow.triggers import trigger_engine

from ai_agent.graph import create_graph


def _setup_test_db(tmp_path: Path):
    db_path = tmp_path / "e2e_growth.db"
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    return engine, session_factory


def _mock_model_outputs(db):
    metrics = calculate_verified_growth_metrics(db)
    first_evidence = metrics.signals[0].evidence_ids[0]
    company = CompanyAnalysis(
        summary="Anka Endüstriyel Otomasyon A.Ş. has a strong industrial base in Turkey.",
        segments=["Industrial Automation", "Robotics & SCADA"],
        strengths=[
            MaterialClaim(
                id="strength-anka-001",
                text="Anka-PLC-5000 and SCADA v4.2 drive major industrial accounts.",
                evidence_ids=[first_evidence],
            )
        ],
        weaknesses=[
            MaterialClaim(
                id="weakness-anka-001",
                text="Support response times need optimization across remote regions.",
                evidence_ids=[first_evidence],
            )
        ],
        data_gaps=["Consent metadata is not fully recorded."],
    )
    hypotheses = OpportunityHypotheses(
        hypotheses=[
            OpportunityHypothesis(
                signal_id=signal.id,
                title=f"Validated Route for Anka: {signal.title}",
                rationale="Verified against persisted CRM and ERP records for Anka Endüstriyel Otomasyon A.Ş.",
                evidence_ids=[signal.evidence_ids[0]],
            )
            for signal in metrics.signals
        ]
    )
    claims = _material_claims(metrics, company, hypotheses)
    review = EvidenceReview(
        approved=True,
        decisions=[
            EvidenceDecision(
                claim_id=claim.id,
                supported=True,
                evidence_ids=[claim.evidence_ids[0]],
                reason="Immutable evidence locator verifies claim for Anka Endüstriyel Otomasyon A.Ş.",
            )
            for claim in claims
        ],
        contradictions=[],
    )
    change_set = OKFChangeSet(
        summary="Update OKF wiki with Anka Endüstriyel Otomasyon A.Ş. Growth Diagnostic summary.",
        concept_paths=["reports/growth-diagnostic.md"],
        source_ids=["src-crm-001", "src-erp-001"],
    )
    return {
        "company-analyst": TestModel(
            call_tools=[], custom_output_args=company.model_dump(mode="json")
        ),
        "growth-opportunity-analyst": TestModel(
            call_tools=[], custom_output_args=hypotheses.model_dump(mode="json")
        ),
        "evidence-reviewer": TestModel(
            call_tools=[], custom_output_args=review.model_dump(mode="json")
        ),
        "wiki-curator": TestModel(
            call_tools=[], custom_output_args=change_set.model_dump(mode="json")
        ),
    }


def test_step_1_webhook_event_simulation_for_anka():
    """Step 1: Simulate webhook event POST /api/webhooks/src-crm-001 for Anka Endüstriyel Otomasyon A.Ş."""
    client = TestClient(app)
    payload = {
        "event_type": "inbound.form_submitted",
        "data": {
            "company_name": "Anka Endüstriyel Otomasyon A.Ş.",
            "contact_email": "info@anka-otomasyon.com.tr",
            "intent_score": 95,
            "region": "Kocaeli",
        },
    }
    response = client.post("/api/webhooks/src-crm-001", json=payload)
    assert response.status_code == 202
    res_data = response.json()
    assert res_data["status"] == "triggered"
    assert res_data["matched_rules_count"] >= 1
    assert "builtin-inbound-triage" in res_data["triggered_workflows"]
    assert res_data["event_id"].startswith("evt-")


def test_step_2_trigger_rule_matching():
    """Step 2: Verify trigger rule matching via trigger_engine.match_rules."""
    matched_inbound = trigger_engine.match_rules("inbound.form_submitted")
    assert len(matched_inbound) >= 1
    assert any(r.target_workflow_id == "builtin-inbound-triage" for r in matched_inbound)

    matched_crm = trigger_engine.match_rules("crm.account_updated")
    assert len(matched_crm) >= 1
    assert any(r.target_workflow_id == "builtin-crm-erp-hygiene" for r in matched_crm)

    matched_competitor = trigger_engine.match_rules("competitor.signal_detected")
    assert len(matched_competitor) >= 1
    assert any(r.target_workflow_id == "builtin-competitive-battlecard" for r in matched_competitor)


def test_step_3_stategraph_execution_all_7_kds_agents():
    """Step 3: Run and verify StateGraph execution across all 7 KDS AI ABS Agent Nodes."""
    graph = create_graph()
    initial_state = {
        "messages": ["Execute complete KDS AI ABS diagnostic for Anka Endüstriyel Otomasyon A.Ş."],
        "company_name": "Anka Endüstriyel Otomasyon A.Ş.",
    }
    result = graph.invoke(initial_state)
    assert "messages" in result
    # Verify outputs from all 7 specialized nodes
    assert result.get("company_profiling_data") is not None
    assert result.get("lead_opportunity_data") is not None
    assert result.get("competitor_intelligence_data") is not None
    assert result.get("security_audit_data") is not None
    assert result.get("financial_diagnostics_data") is not None
    assert result.get("seo_brand_intelligence_data") is not None
    assert result.get("customer_satisfaction_data") is not None


def test_step_4_5_6_full_persisted_workflow_and_approval_candidate_lifecycle(tmp_path: Path):
    """Steps 4, 5 & 6:
    Step 4: Evidence grounding locators (ev_...) computed & linked in DB / _enforce_evidence_gate.
    Step 5: Human approval candidate (ApprovalRequest & OKFCandidate) generated in DB.
    Step 6: Approval decision recording (approve_candidate / decide_persisted_approval) and OKF wiki patch.
    """
    engine, local_session = _setup_test_db(tmp_path)
    knowledge_root = tmp_path / "knowledge"
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'e2e_growth.db').as_posix()}",
        knowledge_root=knowledge_root,
        model_profile="local-balanced",
    )

    with local_session() as db:
        # Ingest demo data for Anka Endüstriyel Otomasyon A.Ş.
        sync_summary = sync_demo_company(db, settings.raw_root)
        assert sync_summary.total_records > 0

        # Verify evidence locators in DB
        evidence_items = list(db.scalars(select(EvidenceItem)))
        assert len(evidence_items) > 0
        assert all(item.id.startswith("ev-") or item.id.startswith("ev_") for item in evidence_items)

        ensure_active_repository(settings.company_bundle)
        ensure_platform_registry(db)

        # Get published workflow definition
        default_wf = build_default_workflow()
        wf_row = db.get(WorkflowDefinitionRow, (default_wf.id, default_wf.version))
        assert wf_row is not None and wf_row.status == "published"

        model_overrides = _mock_model_outputs(db)

        # Execute workflow run
        run = asyncio.run(
            start_persisted_workflow(
                db,
                settings,
                wf_row,
                idempotency_key="e2e-anka-simulation-001",
                actor_id="admin-test",
                model_overrides=model_overrides,
            )
        )

        # Verify workflow run state
        assert run.status == "awaiting_approval"
        assert run.evidence_ids is not None
        assert len(run.evidence_ids) > 0

        # Step 4 check: Evidence grounding locators linked
        for ev_id in run.evidence_ids:
            ev_row = db.get(EvidenceItem, ev_id)
            assert ev_row is not None
            assert ev_row.id.startswith("ev_") or ev_row.id.startswith("ev-")

        # Step 5 check: OKFCandidate and ApprovalRequest created
        candidate = db.scalar(select(OKFCandidate).where(OKFCandidate.run_id == run.id))
        assert candidate is not None
        assert candidate.status == "pending"

        approval = db.scalar(select(ApprovalRequest).where(ApprovalRequest.run_id == run.id))
        assert approval is not None
        assert approval.status == "pending"
        assert approval.candidate_id == candidate.id

        # Step 6 check: Approval decision recording & OKF wiki patch proposal
        before_git_rev = GitKnowledgeRepository(settings.company_bundle).ensure_baseline()

        resumed_run, qmd_result = asyncio.run(
            decide_persisted_approval(
                db,
                settings,
                approval,
                decision="approved",
                reason="Verified e2e evidence grounding and diagnostic output for Anka Endüstriyel Otomasyon A.Ş.",
                actor_id="approver-test",
                idempotency_key="e2e-approval-decision-001",
            )
        )

        assert resumed_run.status == "completed"
        assert approval.status == "approved"
        assert candidate.status == "approved"

        after_git_rev = GitKnowledgeRepository(settings.company_bundle).ensure_baseline()
        assert after_git_rev != before_git_rev

    engine.dispose()
