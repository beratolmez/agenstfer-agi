import asyncio
import json
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
from agi_server.agents.probe import probe_model_profile
from agi_server.agents.registry import AgentRegistry
from agi_server.agents.runtime import AgentExecution, ScopedCapabilityTools
from agi_server.config import Settings
from agi_server.db import (
    Artifact,
    Base,
    CanonicalEntity,
    EvidenceItem,
    OKFCandidate,
    WorkflowRun,
    WorkflowStepRun,
)
from agi_server.diagnostics.service import (
    _evidence_prompt_view,
    _evidence_review_batches,
    _material_claims,
    _metric_prompt_view,
    _run_evidence_reviewer,
    _signal_prompt_view,
    run_growth_diagnostic,
)
from agi_server.domain.computed_diagnostic import build_computed_diagnostic
from agi_server.domain.metrics import (
    calculate_growth_metrics,
    calculate_verified_growth_metrics,
)
from agi_server.ingestion import resolve_evidence_excerpt, sync_demo_company
from agi_server.main import dashboard
from agi_server.okf.lifecycle import ensure_active_repository
from pydantic_ai.models.test import TestModel
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker


def _session(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'diagnostic.db').as_posix()}")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def _typed_outputs(db):
    metrics = calculate_verified_growth_metrics(db)
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
        assert all(
            "verification_source_evidence_ids" not in item
            for item in _signal_prompt_view(after)
        )
    engine.dispose()


def test_dashboard_has_no_synthetic_fallback_before_a_successful_run(tmp_path: Path) -> None:
    engine, local_session = _session(tmp_path)
    with local_session() as db:
        sync_demo_company(db, tmp_path / "knowledge" / "raw")
        assert dashboard(db) is None
    engine.dispose()


def test_dashboard_reads_the_persisted_durable_growth_workflow(tmp_path: Path) -> None:
    engine, local_session = _session(tmp_path)
    with local_session() as db:
        sync_demo_company(db, tmp_path / "knowledge" / "raw")
        metrics, company, hypotheses, _, _ = _typed_outputs(db)
        run = WorkflowRun(
            idempotency_key="durable-dashboard-001",
            workflow_id="builtin-growth-diagnostic",
            workflow_version=2,
            status="awaiting_approval",
        )
        db.add(run)
        db.commit()
        diagnostic = build_computed_diagnostic(db, run.id, metrics, company, hypotheses)
        run.output_json = {"diagnostic": diagnostic.model_dump(mode="json")}
        db.commit()

        result = dashboard(db)

        assert result is not None
        assert result.id == diagnostic.id
        assert len(result.opportunities) == 5
    engine.dispose()


def test_evidence_prompt_view_keeps_verification_fields_without_duplicate_metadata(
    tmp_path: Path,
) -> None:
    engine, local_session = _session(tmp_path)
    knowledge_root = tmp_path / "knowledge"
    with local_session() as db:
        sync_demo_company(db, knowledge_root / "raw")
        metrics = calculate_growth_metrics(db)
        evidence_id = metrics.signals[0].evidence_ids[0]
        row = db.get(EvidenceItem, evidence_id)
        assert row is not None
        tools = ScopedCapabilityTools(
            db,
            metrics,
            knowledge_root,
            knowledge_root / "bundles" / "company",
            cloud=False,
        )
        resolved = tools.read_evidence(evidence_id)
        view = _evidence_prompt_view(row, resolved)

        assert set(view) == {
            "locator",
            "excerpt_hash",
            "excerpt",
        }
        assert view["excerpt"] == resolved["excerpt"]
        assert "snapshot_id" not in view
        assert "collected_at" not in view
    engine.dispose()


def test_deterministic_metric_receipts_bind_aggregate_claims_to_source_evidence(
    tmp_path: Path,
) -> None:
    engine, local_session = _session(tmp_path)
    raw_root = tmp_path / "knowledge" / "raw"
    with local_session() as db:
        sync_demo_company(db, raw_root)
        metrics = calculate_verified_growth_metrics(db)
        db.commit()

        assert all(signal.verification_evidence_id for signal in metrics.signals)
        assert len({signal.verification_evidence_id for signal in metrics.signals}) == 5
        for signal in metrics.signals:
            evidence_id = signal.verification_evidence_id
            assert evidence_id is not None
            row = db.get(EvidenceItem, evidence_id)
            assert row is not None
            assert row.locator["kind"] == "deterministic_metric"
            assert row.locator["source_evidence_ids"] == sorted(
                set(signal.verification_source_evidence_ids)
            )
            resolved = resolve_evidence_excerpt(db, raw_root, evidence_id)
            assert resolved is not None
            assert resolved["excerpt"]["metrics"] == signal.metrics
            assert resolved["excerpt"]["score"] == signal.factors.total()
            assert resolved["excerpt"]["source_evidence_count"] == len(
                signal.verification_source_evidence_ids
            )
            prompt_view = _evidence_prompt_view(row, resolved)
            assert "source_evidence_ids" not in prompt_view["locator"]

        assert any(
            len(signal.verification_source_evidence_ids) > len(signal.evidence_ids)
            for signal in metrics.signals
        )

        company = CompanyAnalysis(
            summary="A sufficiently bounded company analysis for deterministic receipt testing.",
            segments=["Industrial automation"],
            strengths=[
                MaterialClaim(
                    id="strength-test",
                    text="A raw row supports this qualitative strength.",
                    evidence_ids=[metrics.signals[0].evidence_ids[0]],
                )
            ],
            weaknesses=[
                MaterialClaim(
                    id="weakness-test",
                    text="A raw row supports this qualitative weakness.",
                    evidence_ids=[metrics.signals[0].evidence_ids[0]],
                )
            ],
            data_gaps=[],
        )
        hypotheses = OpportunityHypotheses(
            hypotheses=[
                OpportunityHypothesis(
                    signal_id=signal.id,
                    title=signal.title,
                    rationale="The persisted source records support this bounded route.",
                    evidence_ids=[signal.evidence_ids[0]],
                )
                for signal in metrics.signals
            ]
        )
        metric_claims = _material_claims(metrics, company, hypotheses)[-5:]
        assert [claim.evidence_ids for claim in metric_claims] == [
            [signal.verification_evidence_id] for signal in metrics.signals
        ]
        with pytest.raises(
            ValueError, match="has no deterministic verification receipt"
        ):
            _material_claims(calculate_growth_metrics(db), company, hypotheses)

        first_receipt_id = metrics.signals[0].verification_evidence_id
        assert first_receipt_id is not None
        first_receipt = db.get(EvidenceItem, first_receipt_id)
        assert first_receipt is not None
        member = db.get(EvidenceItem, first_receipt.locator["source_evidence_ids"][0])
        assert member is not None
        original_classification = member.classification
        member.classification = "unknown-secret"
        db.flush()
        with pytest.raises(
            ValueError, match="Metric source evidence has invalid classifications"
        ):
            calculate_verified_growth_metrics(db)
        member.classification = original_classification
        original_excerpt_hash = member.excerpt_hash
        member.excerpt_hash = "0" * 64
        db.flush()
        with pytest.raises(
            RuntimeError, match="Deterministic metric source evidence digest does not match"
        ):
            resolve_evidence_excerpt(db, raw_root, first_receipt_id)
        member.excerpt_hash = original_excerpt_hash
        db.flush()
        db.delete(member)
        db.flush()
        with pytest.raises(
            RuntimeError, match="Deterministic metric source evidence is missing or invalid"
        ):
            resolve_evidence_excerpt(db, raw_root, first_receipt_id)
    engine.dispose()


def test_evidence_reviewer_batches_real_provider_calls_and_merges_all_claims(
    monkeypatch,
) -> None:
    calls: list[list[str]] = []

    async def fake_run_managed_agent(agent_id, prompt, settings, tools, **kwargs):
        claim_payload = json.loads(
            prompt.split("\nClaims:\n", 1)[1].split("\nEvidence catalog:\n", 1)[0]
        )
        claim_ids = [item["id"] for item in claim_payload]
        calls.append(claim_ids)
        output = EvidenceReview(
            approved=True,
            decisions=[
                EvidenceDecision(
                    claim_id=item["id"],
                    supported=True,
                    evidence_ids=[item["evidence_ids"][0]],
                    reason="The supplied excerpt supports this claim.",
                )
                for item in claim_payload
            ],
            contradictions=[],
        )
        return AgentExecution(
            spec=AgentRegistry().get(agent_id),
            profile_id="local-balanced",
            provider="ollama",
            model_name="qwen3.5:9b",
            output=output,
            usage={"input_tokens": 10, "output_tokens": 10, "requests": 1},
        )

    monkeypatch.setattr(
        "agi_server.diagnostics.service.run_managed_agent", fake_run_managed_agent
    )
    claims = [
        MaterialClaim(
            id=f"claim-{index:03d}",
            text="A material claim backed by persisted evidence.",
            evidence_ids=[f"evidence-{index:03d}"],
        )
        for index in range(11)
    ]
    catalog = {
        f"evidence-{index:03d}": {
            "locator": {"row": index + 1},
            "excerpt_hash": f"hash-{index:03d}",
            "excerpt": {"value": index},
        }
        for index in range(11)
    }

    execution = asyncio.run(
        _run_evidence_reviewer(
            claims,
            catalog,
            Settings(),
            None,
            "local-balanced",
        )
    )

    assert [len(batch) for batch in calls] == [5, 5, 1]
    assert len(execution.output.decisions) == 11
    assert {item.claim_id for item in execution.output.decisions} == {
        item.id for item in claims
    }
    assert execution.usage["requests"] == 3


def test_evidence_reviewer_batches_high_evidence_claims_by_context_budget() -> None:
    claims = [
        MaterialClaim(
            id=f"metric-claim-{index:03d}",
            text="A deterministic numerical claim with representative evidence.",
            evidence_ids=[f"evidence-{index:03d}-{offset}" for offset in range(3)],
        )
        for index in range(5)
    ]

    assert [len(batch) for batch in _evidence_review_batches(claims)] == [2, 2, 1]


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
