import asyncio
from datetime import UTC, datetime
from pathlib import Path

import pytest
from agi_server.agents.contracts import (
    CompanyAnalysis,
    EvidenceDecision,
    EvidenceReview,
    MaterialClaim,
    OKFChangeSet,
    OpportunityHypotheses,
    OpportunityHypothesis,
)
from agi_server.agents.registry import AgentRegistry, ManagedAgentSpec
from agi_server.config import Settings
from agi_server.db import (
    AgentDefinitionRow,
    ApprovalRequest,
    Base,
    CanonicalEntity,
    CapabilityDefinitionRow,
    OKFCandidate,
    WorkflowDefinitionRow,
    WorkflowRun,
    WorkflowStepRun,
)
from agi_server.diagnostics.service import _material_claims
from agi_server.domain.metrics import (
    calculate_verified_growth_metrics,
)
from agi_server.evaluation import (
    prepare_qualification_workflow,
    qualification_provenance,
    summarize_qualification_run,
)
from agi_server.ingestion import sync_demo_company
from agi_server.okf.git_repo import GitKnowledgeRepository
from agi_server.okf.lifecycle import ensure_active_repository
from agi_server.workflow import build_default_workflow, validate_workflow
from agi_server.workflow.models import NodeKind, WorkflowEdge, WorkflowNode
from agi_server.workflow.persistent_runtime import (
    _durable_result,
    decide_persisted_approval,
    evaluate_condition,
    start_persisted_workflow,
)
from agi_server.workflow.registry_service import (
    clone_agent_version,
    clone_workflow_version,
    create_schedule,
    ensure_platform_registry,
    publish_agent,
    publish_workflow,
    save_agent_draft,
    save_workflow_draft,
    workflow_from_row,
)
from agi_server.workflow.scheduler import cron_matches, expire_approvals, run_due_schedules
from pydantic import SecretStr, ValidationError
from pydantic_ai.models.test import TestModel
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker


def _database(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'workflow.db').as_posix()}")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def _models(db):
    metrics = calculate_verified_growth_metrics(db)
    first_evidence = metrics.signals[0].evidence_ids[0]
    company = CompanyAnalysis(
        summary="Persisted Anka data supports multiple evidence-backed growth routes.",
        segments=["Industrial automation"],
        strengths=[
            MaterialClaim(
                id="strength-installed-base",
                text="The installed base supports service expansion.",
                evidence_ids=[first_evidence],
            )
        ],
        weaknesses=[
            MaterialClaim(
                id="weakness-contact-data",
                text="Contact data must be completed before outreach.",
                evidence_ids=[first_evidence],
            )
        ],
        data_gaps=["Consent status is unavailable."],
    )
    hypotheses = OpportunityHypotheses(
        hypotheses=[
            OpportunityHypothesis(
                signal_id=signal.id,
                title=f"Validated {signal.title}",
                rationale="Persisted records support this hypothesis and its unchanged score.",
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
                reason="The immutable record supports the supplied claim.",
            )
            for claim in claims
        ],
        contradictions=[],
    )
    curator = OKFChangeSet(
        summary="Propose a candidate report concept.",
        concept_paths=["reports/growth-diagnostic.md"],
        source_ids=["src-crm-001", "src-erp-001", "src-strategy-001"],
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
            call_tools=[], custom_output_args=curator.model_dump(mode="json")
        ),
    }


def test_registry_versions_are_seeded_cloned_and_immutable(tmp_path: Path) -> None:
    engine, local_session = _database(tmp_path)
    with local_session() as db:
        ensure_platform_registry(db)
        assert db.scalar(select(func.count()).select_from(AgentDefinitionRow)) == 4
        assert db.scalar(select(func.count()).select_from(CapabilityDefinitionRow)) >= 4
        published = db.get(
            WorkflowDefinitionRow,
            (build_default_workflow().id, build_default_workflow().version),
        )
        assert published is not None and published.status == "published"

        draft = clone_workflow_version(db, published, None, target_id="test-growth-diagnostic")
        assert draft.version == 1 and draft.status == "draft"
        definition = workflow_from_row(draft)
        definition.name = "Editable Growth Diagnostic"
        save_workflow_draft(db, definition, None)
        publish_workflow(db, draft)
        assert draft.status == "published"
        with pytest.raises(ValueError, match="immutable"):
            save_workflow_draft(db, definition, None)
        with pytest.raises(ValueError, match="cloning"):
            save_workflow_draft(
                db,
                definition.model_copy(update={"version": 99, "status": "draft"}),
                None,
            )

        agent = db.get(AgentDefinitionRow, ("company-analyst", 3))
        assert agent is not None
        assert agent.definition["max_output_tokens"] == 900
        growth_agent = db.get(AgentDefinitionRow, ("growth-opportunity-analyst", 3))
        assert growth_agent is not None
        assert growth_agent.definition["max_output_tokens"] == 900
        evidence_agent = db.get(AgentDefinitionRow, ("evidence-reviewer", 3))
        assert evidence_agent is not None
        assert evidence_agent.definition["max_output_tokens"] == 1800
        agent_draft = clone_agent_version(db, agent, None)
        assert agent_draft.version == 4
        spec = agent_draft.definition | {"version": agent_draft.version}
        parsed = save_agent_draft(
            db,
            agent_from_payload(spec),
            None,
        )
        publish_agent(db, parsed)
        with pytest.raises(ValueError, match="immutable"):
            save_agent_draft(db, agent_from_payload(spec), None)
        with pytest.raises(ValueError, match="cloning"):
            save_agent_draft(
                db,
                agent_from_payload(spec | {"version": 99}),
                None,
            )
    engine.dispose()


def agent_from_payload(payload):
    return ManagedAgentSpec.model_validate(payload)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("agent_id", "missing-agent", "no published version"),
        ("model_profile", "arbitrary-provider", "not allowlisted"),
        ("output_type", "EvidenceReview", "does not match agent"),
    ],
)
def test_workflow_publish_rejects_invalid_agent_registry_bindings(
    tmp_path: Path, field: str, value: str, message: str
) -> None:
    engine, local_session = _database(tmp_path)
    with local_session() as db:
        ensure_platform_registry(db)
        source = db.get(
            WorkflowDefinitionRow,
            (build_default_workflow().id, build_default_workflow().version),
        )
        assert source is not None
        draft = clone_workflow_version(db, source, None, target_id="binding-test")
        definition = workflow_from_row(draft)
        company = next(node for node in definition.nodes if node.id == "company_agent")
        company.config[field] = value
        save_workflow_draft(db, definition, None)

        with pytest.raises(ValueError, match=message):
            publish_workflow(db, draft)
    engine.dispose()


def test_workflow_publish_pins_exact_agent_versions(tmp_path: Path) -> None:
    engine, local_session = _database(tmp_path)
    with local_session() as db:
        ensure_platform_registry(db)
        source = db.get(
            WorkflowDefinitionRow,
            (build_default_workflow().id, build_default_workflow().version),
        )
        assert source is not None
        draft = clone_workflow_version(db, source, None, target_id="pin-test")
        definition = workflow_from_row(draft)
        for node in definition.nodes:
            node.config.pop("agent_version", None)
        save_workflow_draft(db, definition, None)

        published = publish_workflow(db, draft)
        pinned = workflow_from_row(published)

        assert {
            str(node.config["agent_id"]): node.config["agent_version"]
            for node in pinned.nodes
            if node.kind == NodeKind.AGENT_RUN
        } == {
            "company-analyst": 3,
            "growth-opportunity-analyst": 3,
            "evidence-reviewer": 3,
            "wiki-curator": 2,
        }
    engine.dispose()


def test_qualification_workflow_pins_profile_agents_and_effective_prompt_hashes(
    tmp_path: Path,
) -> None:
    engine, local_session = _database(tmp_path)
    with local_session() as db:
        workflow = prepare_qualification_workflow(db, "local-strong")
        definition = workflow_from_row(workflow)
        provenance = qualification_provenance(db, workflow)

        assert workflow.id == "qualification-local-strong"
        assert workflow.status == "published"
        assert {
            node.config["model_profile"]
            for node in definition.nodes
            if node.kind == NodeKind.AGENT_RUN
        } == {"local-strong"}
        assert provenance["qualification_path"] == "published-persistent-workflow-v1"
        assert provenance["workflow"] == {"id": workflow.id, "version": 1}
        assert len(provenance["workflow_definition_sha256"]) == 64
        assert set(provenance["agent_versions"]) == {
            "company-analyst",
            "growth-opportunity-analyst",
            "evidence-reviewer",
            "wiki-curator",
        }
        assert set(provenance["agent_model_profiles"].values()) == {"local-strong"}
        assert all(len(digest) == 64 for digest in provenance["effective_prompt_sha256"].values())
    engine.dispose()


def test_cloud_qualification_blocks_restricted_canonical_scope_before_model(
    tmp_path: Path,
) -> None:
    engine, local_session = _database(tmp_path)
    knowledge_root = tmp_path / "knowledge"
    settings = Settings(
        knowledge_root=knowledge_root,
        cloud_models_enabled=True,
        cloud_provider="groq",
        cloud_api_key=SecretStr("test-key"),
    )
    with local_session() as db:
        sync_demo_company(db, settings.raw_root)
        db.add(
            CanonicalEntity(
                id="restricted-account",
                entity_type="accounts",
                classification="restricted",
            )
        )
        db.commit()
        workflow = prepare_qualification_workflow(db, "cloud-balanced")

        with pytest.raises(PermissionError, match="restricted diagnostic data"):
            asyncio.run(
                start_persisted_workflow(
                    db,
                    settings,
                    workflow,
                    "cloud-restricted-scope",
                    None,
                )
            )

        run = db.scalar(
            select(WorkflowRun).where(WorkflowRun.idempotency_key == "cloud-restricted-scope")
        )
        assert run is not None and run.status == "failed"
        blocked_step = db.scalar(
            select(WorkflowStepRun).where(
                WorkflowStepRun.run_id == run.id,
                WorkflowStepRun.agent_id == "company-analyst",
            )
        )
        assert blocked_step is not None
        assert blocked_step.status == "failed"
        assert blocked_step.model_provider == "groq"
        assert blocked_step.data_classification == "restricted"
        assert blocked_step.redaction_applied is False
        assert blocked_step.token_usage is None
    engine.dispose()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("model_profile", "arbitrary-provider"),
        ("output_type", "ShellCommand"),
        ("data_classification", "unknown"),
        ("approval_risk", "critical"),
        ("capabilities", ["context.query", "context.query"]),
    ],
)
def test_agent_drafts_reject_non_allowlisted_contract_values(field: str, value) -> None:
    payload = AgentRegistry().get("company-analyst").model_dump()
    payload[field] = value

    with pytest.raises(ValidationError):
        ManagedAgentSpec.model_validate(payload)


def test_condition_contract_rejects_expressions_and_duplicate_branches() -> None:
    workflow = build_default_workflow()
    condition = WorkflowNode(
        id="safe_condition",
        kind=NodeKind.CONDITION,
        label="Safe condition",
        position={"x": 0, "y": 0},
        config={"expression": "__import__('os')"},
        output_type="control",
    )
    workflow.nodes.append(condition)
    workflow.edges.extend(
        [
            WorkflowEdge(
                id="bad-branch-1",
                source="safe_condition",
                target="report",
                data_type="control",
                branch="true",
            ),
            WorkflowEdge(
                id="bad-branch-2",
                source="safe_condition",
                target="report",
                data_type="control",
                branch="true",
            ),
        ]
    )
    result = validate_workflow(workflow)
    assert not result.valid
    assert {item.code for item in result.issues}.issuperset(
        {"node.missing_config", "condition.branches"}
    )
    assert evaluate_condition(
        {"scores": {"energy": 75}},
        {"field": "scores.energy", "operator": "gte", "value": 70},
    )


def test_schedule_uses_timezone_and_prevents_duplicate_minute_runs(
    tmp_path: Path, monkeypatch
) -> None:
    engine, local_session = _database(tmp_path)
    settings = Settings(knowledge_root=tmp_path / "knowledge")
    with local_session() as db:
        ensure_platform_registry(db)
        workflow = db.get(
            WorkflowDefinitionRow,
            (build_default_workflow().id, build_default_workflow().version),
        )
        assert workflow is not None
        schedule = create_schedule(db, workflow, "15 9 * * 1-5", "Europe/Istanbul", None)
        instant = datetime(2026, 7, 13, 6, 15, tzinfo=UTC)
        assert cron_matches(schedule.cron, instant, schedule.timezone)

        class Run:
            id = "run-scheduled"

        calls = 0

        async def fake_start(*args, **kwargs):
            nonlocal calls
            calls += 1
            return Run()

        monkeypatch.setattr("agi_server.workflow.scheduler.start_persisted_workflow", fake_start)
        first = asyncio.run(run_due_schedules(db, settings, instant))
        second = asyncio.run(run_due_schedules(db, settings, instant))
        assert first == ["run-scheduled"] and second == []
        assert calls == 1
        assert schedule.last_fire_key is not None
    engine.dispose()


def test_published_workflow_pauses_and_resumes_after_restart(tmp_path: Path) -> None:
    engine, local_session = _database(tmp_path)
    knowledge_root = tmp_path / "knowledge"
    settings = Settings(
        knowledge_root=knowledge_root,
        qmd_url=None,
        model_profile="cloud-balanced",
        cloud_models_enabled=True,
        cloud_provider="groq",
        cloud_api_key=SecretStr("test-key"),
    )
    with local_session() as db:
        sync_demo_company(db, settings.raw_root)
        ensure_active_repository(settings.company_bundle)
        ensure_platform_registry(db)
        models = _models(db)
        workflow = db.get(
            WorkflowDefinitionRow,
            (build_default_workflow().id, build_default_workflow().version),
        )
        assert workflow is not None
        run = asyncio.run(
            start_persisted_workflow(
                db,
                settings,
                workflow,
                "workflow-restart-001",
                None,
                model_overrides=models,
            )
        )
        assert run.status == "awaiting_approval"
        assert run.model_profile == "local-balanced"
        assert run.agent_versions == {
            "company-analyst": 3,
            "growth-opportunity-analyst": 3,
            "evidence-reviewer": 3,
            "wiki-curator": 2,
        }
        approval_id = db.scalar(select(ApprovalRequest.id).where(ApprovalRequest.run_id == run.id))
        assert approval_id is not None
        assert db.scalar(
            select(func.count())
            .select_from(WorkflowStepRun)
            .where(WorkflowStepRun.run_id == run.id)
        ) == len(build_default_workflow().nodes)
        assert set(
            db.scalars(
                select(WorkflowStepRun.agent_id).where(
                    WorkflowStepRun.run_id == run.id,
                    WorkflowStepRun.agent_id.is_not(None),
                )
            )
        ) == {
            "company-analyst",
            "growth-opportunity-analyst",
            "evidence-reviewer",
            "wiki-curator",
        }
        assert {
            row.agent_id: row.agent_version
            for row in db.scalars(
                select(WorkflowStepRun).where(
                    WorkflowStepRun.run_id == run.id,
                    WorkflowStepRun.agent_id.is_not(None),
                )
            )
        } == run.agent_versions
        assert run.output_json["okf_change_set"]["concept_paths"] == [
            "reports/growth-diagnostic.md"
        ]
        qualification = summarize_qualification_run(run)
        assert qualification["material_claim_count"] == qualification["supported_claim_count"]
        assert qualification["evidence_coverage"] == 100
        assert qualification["unsupported_numerical_claims"] == 0
        duplicate = asyncio.run(
            start_persisted_workflow(
                db,
                settings,
                workflow,
                "workflow-restart-001",
                None,
                model_overrides=models,
            )
        )
        assert duplicate.id == run.id
        run_id = run.id
        candidate_id = db.scalar(select(OKFCandidate.id).where(OKFCandidate.run_id == run.id))
        assert candidate_id is not None
        before_revision = GitKnowledgeRepository(settings.company_bundle).ensure_baseline()

    with local_session() as restarted_db:
        approval = restarted_db.get(ApprovalRequest, approval_id)
        assert approval is not None
        approval.status = "decision_submitted"
        approval.decision_idempotency_key = "approval-decision-001"
        approval.decision_reason = "Evidence and candidate diff were reviewed."
        restarted_db.commit()
        recovery_run = restarted_db.get(WorkflowRun, run.id)
        assert recovery_run is not None
        assert _durable_result(restarted_db, recovery_run)["approval_id"] == approval.id
        with pytest.raises(ValueError, match="stale"):
            asyncio.run(
                decide_persisted_approval(
                    restarted_db,
                    settings,
                    approval,
                    decision="approved",
                    reason="A second decision must not replace the reserved one.",
                    actor_id=None,
                    idempotency_key="approval-decision-002",
                )
            )
        resumed, qmd = asyncio.run(
            decide_persisted_approval(
                restarted_db,
                settings,
                approval,
                decision="approved",
                reason="Evidence and candidate diff were reviewed.",
                actor_id=None,
                idempotency_key="approval-decision-001",
            )
        )
        assert resumed.id == run_id and resumed.status == "completed"
        assert qmd == "disabled; lexical fallback active"
        assert restarted_db.get(OKFCandidate, candidate_id).status == "approved"
        after_revision = GitKnowledgeRepository(settings.company_bundle).ensure_baseline()
        assert after_revision != before_revision

        repeated, result = asyncio.run(
            decide_persisted_approval(
                restarted_db,
                settings,
                approval,
                decision="approved",
                reason="Evidence and candidate diff were reviewed.",
                actor_id=None,
                idempotency_key="approval-decision-001",
            )
        )
        assert repeated.id == run_id and result == "duplicate"
    engine.dispose()


def test_rejected_workflow_candidate_never_changes_active_revision(tmp_path: Path) -> None:
    engine, local_session = _database(tmp_path)
    settings = Settings(knowledge_root=tmp_path / "knowledge", qmd_url=None)
    with local_session() as db:
        sync_demo_company(db, settings.raw_root)
        ensure_active_repository(settings.company_bundle)
        ensure_platform_registry(db)
        workflow = db.get(
            WorkflowDefinitionRow,
            (build_default_workflow().id, build_default_workflow().version),
        )
        run = asyncio.run(
            start_persisted_workflow(
                db,
                settings,
                workflow,
                "workflow-reject-001",
                None,
                model_overrides=_models(db),
            )
        )
        approval = db.scalar(select(ApprovalRequest).where(ApprovalRequest.run_id == run.id))
        assert approval is not None
        before = GitKnowledgeRepository(settings.company_bundle).ensure_baseline()
        rejected, qmd = asyncio.run(
            decide_persisted_approval(
                db,
                settings,
                approval,
                decision="rejected",
                reason="The candidate requires additional business review.",
                actor_id=None,
                idempotency_key="approval-reject-001",
            )
        )
        assert rejected.status == "rejected" and qmd == "unchanged"
        assert GitKnowledgeRepository(settings.company_bundle).ensure_baseline() == before
        candidate = db.scalar(select(OKFCandidate).where(OKFCandidate.run_id == run.id))
        assert candidate is not None and candidate.status == "rejected"
    engine.dispose()


def test_submitted_approval_expiry_closes_run_step_and_candidate(tmp_path: Path) -> None:
    engine, local_session = _database(tmp_path)
    settings = Settings(knowledge_root=tmp_path / "knowledge", qmd_url=None)
    with local_session() as db:
        sync_demo_company(db, settings.raw_root)
        ensure_active_repository(settings.company_bundle)
        ensure_platform_registry(db)
        workflow = db.get(
            WorkflowDefinitionRow,
            (build_default_workflow().id, build_default_workflow().version),
        )
        run = asyncio.run(
            start_persisted_workflow(
                db,
                settings,
                workflow,
                "workflow-expiry-001",
                None,
                model_overrides=_models(db),
            )
        )
        approval = db.scalar(select(ApprovalRequest).where(ApprovalRequest.run_id == run.id))
        assert approval is not None
        approval.status = "decision_submitted"
        approval.expires_at = datetime(2026, 7, 13, tzinfo=UTC)
        db.commit()

        assert expire_approvals(db, datetime(2026, 7, 14, tzinfo=UTC)) == 1
        assert approval.status == "expired"
        assert run.status == "expired"
        candidate = db.scalar(select(OKFCandidate).where(OKFCandidate.run_id == run.id))
        assert candidate is not None and candidate.status == "expired"
        step = db.scalar(
            select(WorkflowStepRun).where(
                WorkflowStepRun.run_id == run.id,
                WorkflowStepRun.step_id == "approval",
            )
        )
        assert step is not None and step.status == "expired"
    engine.dispose()
