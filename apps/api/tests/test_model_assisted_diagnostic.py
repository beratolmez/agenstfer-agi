import asyncio
from pathlib import Path

from agi_server.agents.contracts import (
    CompanyAnalysis,
    EvidenceDecision,
    EvidenceReview,
    MaterialClaim,
    OKFChangeSet,
    OpportunityHypotheses,
    OpportunityHypothesis,
)
from agi_server.agents.probe import probe_model_profile
from agi_server.agents.runtime import ScopedCapabilityTools
from agi_server.config import Settings
from agi_server.db import (
    Artifact,
    Base,
    CanonicalEntity,
    OKFCandidate,
    WorkflowRun,
    WorkflowStepRun,
)
from agi_server.diagnostics.service import (
    _material_claims,
    _metric_prompt_view,
    _signal_prompt_view,
    run_growth_diagnostic,
)
from agi_server.domain.metrics import calculate_growth_metrics
from agi_server.ingestion import sync_demo_company
from agi_server.okf.lifecycle import ensure_active_repository
from pydantic_ai.models.test import TestModel
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker


def _session(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'diagnostic.db').as_posix()}")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def _typed_outputs(db):
    metrics = calculate_growth_metrics(db)
    first_evidence = metrics.signals[0].evidence_ids[0]
    company = CompanyAnalysis(
        summary="Anka has a measurable installed base and five evidence-backed growth routes.",
        segments=["Industrial automation", "Export-ready accounts"],
        strengths=[
            MaterialClaim(
                id="strength-installed-base",
                text="The installed base supports service expansion.",
                evidence_ids=[first_evidence],
            )
        ],
        weaknesses=[
            MaterialClaim(
                id="weakness-contact-quality",
                text="Contact completeness requires remediation before outreach.",
                evidence_ids=[first_evidence],
            )
        ],
        data_gaps=["Consent status is not represented in the demo data."],
    )
    hypotheses = OpportunityHypotheses(
        hypotheses=[
            OpportunityHypothesis(
                signal_id=signal.id,
                title=f"Validated route: {signal.title}",
                rationale=(
                    "Persisted source records support this route; the deterministic score "
                    "is retained without model alteration."
                ),
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
                reason="The cited immutable source record supports the material claim.",
            )
            for claim in claims
        ],
        contradictions=[],
    )
    change_set = OKFChangeSet(
        summary="Create the evidence-reviewed Growth Diagnostic report concept.",
        concept_paths=["reports/growth-diagnostic.md"],
        source_ids=["src-crm-001", "src-erp-001", "src-strategy-001"],
    )
    return metrics, company, hypotheses, review, change_set


def test_growth_metrics_are_derived_from_persisted_entities(tmp_path: Path) -> None:
    engine, local_session = _session(tmp_path)
    with local_session() as db:
        sync_demo_company(db, tmp_path / "knowledge" / "raw")
        before = calculate_growth_metrics(db)
        account = db.scalar(
            select(CanonicalEntity).where(CanonicalEntity.entity_type == "accounts")
        )
        assert account is not None
        was_high_energy = float(account.attributes.get("energy_intensity", 0)) >= 0.75
        account.attributes = {**account.attributes, "energy_intensity": 0.99}
        db.commit()

        after = calculate_growth_metrics(db)
        expected_delta = 0 if was_high_energy else 1
        assert (
            after.metrics["high_energy_accounts"].value
            == before.metrics["high_energy_accounts"].value + expected_delta
        )
        assert after.counts.accounts == 150
        assert len(after.signals) == 5
        assert len(after.planted_insights) >= 5
        assert all(signal.evidence_ids for signal in after.signals)
        assert all(
            len(item["representative_evidence_ids"]) <= 3
            for item in _metric_prompt_view(after)["metrics"].values()
        )
        assert all(len(item["evidence_ids"]) <= 3 for item in _signal_prompt_view(after))
    engine.dispose()


def test_structured_output_probe_checks_the_nonce(monkeypatch) -> None:
    nonce = "00000000-0000-0000-0000-000000000001"
    monkeypatch.setattr("agi_server.agents.probe._new_probe_nonce", lambda: nonce)
    result = asyncio.run(
        probe_model_profile(
            Settings(model_profile="local-balanced"),
            "local-balanced",
            model_override=TestModel(
                call_tools=[],
                custom_output_args={"status": "ok", "nonce": nonce},
            ),
        )
    )

    assert result["ready"] is True
    assert result["structured_output"] is True
    assert result["usage"]["requests"] == 1


def test_invalid_model_tool_arguments_return_bounded_rejections(tmp_path: Path) -> None:
    engine, local_session = _session(tmp_path)
    with local_session() as db:
        sync_demo_company(db, tmp_path / "knowledge" / "raw")
        tools = ScopedCapabilityTools(
            db,
            calculate_growth_metrics(db),
            tmp_path / "knowledge",
            tmp_path / "knowledge" / "bundles" / "company",
            cloud=False,
        )

        metric = tools.calculate_metric("invented_metric")
        evidence = tools.read_evidence("invented-evidence")
        patch = tools.propose_okf_patch("../outside.md", "Invalid traversal")

        assert metric["status"] == "rejected"
        assert metric["allowed_metric_keys"]
        assert evidence == {"status": "rejected", "reason": "evidence_not_found"}
        assert patch["status"] == "rejected-invalid-path"
    engine.dispose()


def test_model_assisted_diagnostic_persists_run_steps_evidence_and_artifacts(
    tmp_path: Path,
) -> None:
    engine, local_session = _session(tmp_path)
    knowledge_root = tmp_path / "knowledge"
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'diagnostic.db').as_posix()}",
        knowledge_root=knowledge_root,
        model_profile="local-balanced",
    )
    with local_session() as db:
        sync_demo_company(db, settings.raw_root)
        ensure_active_repository(settings.company_bundle)
        metrics, company, hypotheses, review, change_set = _typed_outputs(db)
        overrides = {
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

        result = asyncio.run(
            run_growth_diagnostic(
                db,
                settings,
                actor_id=None,
                idempotency_key="test-diagnostic-001",
                model_overrides=overrides,
            )
        )

        assert result.run.status == "awaiting_approval"
        assert result.run.model_profile == "local-balanced"
        assert result.run.token_usage["requests"] == 4
        assert result.run.evidence_ids
        assert result.diagnostic.counts == metrics.counts
        assert len(result.diagnostic.opportunities) == 5
        assert all(item.evidence for item in result.diagnostic.opportunities)
        steps = list(
            db.scalars(
                select(WorkflowStepRun)
                .where(WorkflowStepRun.run_id == result.run.id)
                .order_by(WorkflowStepRun.sequence)
            )
        )
        assert [step.step_id for step in steps] == [
            "deterministic-metrics",
            "company-analyst",
            "growth-opportunity-analyst",
            "evidence-reviewer",
            "wiki-curator",
        ]
        assert all(step.status == "completed" for step in steps)
        artifacts = list(db.scalars(select(Artifact).where(Artifact.run_id == result.run.id)))
        assert {artifact.kind for artifact in artifacts} == {
            "diagnostic-markdown",
            "diagnostic-html",
            "okf-candidate-diff",
        }
        for artifact in artifacts:
            if artifact.kind.startswith("diagnostic-"):
                assert (knowledge_root / artifact.uri).is_file()
        candidate = db.scalar(select(OKFCandidate).where(OKFCandidate.run_id == result.run.id))
        assert candidate is not None and candidate.status == "pending"

        repeated = asyncio.run(
            run_growth_diagnostic(
                db,
                settings,
                actor_id=None,
                idempotency_key="test-diagnostic-001",
                model_overrides=overrides,
            )
        )
        assert repeated.run.id == result.run.id
        assert db.query(WorkflowRun).count() == 1
    engine.dispose()


def test_evidence_rejection_fails_without_creating_candidate(tmp_path: Path) -> None:
    engine, local_session = _session(tmp_path)
    knowledge_root = tmp_path / "knowledge"
    settings = Settings(knowledge_root=knowledge_root, model_profile="local-balanced")
    with local_session() as db:
        sync_demo_company(db, settings.raw_root)
        ensure_active_repository(settings.company_bundle)
        _, company, hypotheses, review, change_set = _typed_outputs(db)
        review.approved = False
        review.decisions[0].supported = False
        overrides = {
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

        try:
            asyncio.run(
                run_growth_diagnostic(
                    db,
                    settings,
                    actor_id=None,
                    idempotency_key="test-diagnostic-rejected",
                    model_overrides=overrides,
                )
            )
        except ValueError as error:
            assert "Evidence review rejected" in str(error)
        else:
            raise AssertionError("Evidence rejection must fail the diagnostic run")

        run = db.scalar(
            select(WorkflowRun).where(WorkflowRun.idempotency_key == "test-diagnostic-rejected")
        )
        assert run is not None and run.status == "failed"
        assert db.scalar(select(OKFCandidate).where(OKFCandidate.run_id == run.id)) is None
    engine.dispose()
