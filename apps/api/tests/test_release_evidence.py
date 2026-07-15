from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from agi_server.release_evidence import (
    ReleaseEvidenceError,
    build_release_manifest,
    validate_qualification_report,
    validate_restart_evidence,
)


def _qualification_report(attempts: int = 20) -> dict[str, object]:
    attempt_results = [
        {
            "attempt": attempt,
            "status": "passed",
            "material_claim_count": 15,
            "supported_claim_count": 15,
            "unsupported_numerical_claims": 0,
            "token_usage": {"input_tokens": 100, "output_tokens": 50},
        }
        for attempt in range(1, attempts + 1)
    ]
    return {
        "profile": "local-strong",
        "provider": "ollama",
        "model": "qwen3.5:27b",
        "attempts": attempts,
        "successful_runs": attempts,
        "success_rate": 1.0,
        "minimum_planted_cases": 5,
        "minimum_evidence_coverage": 100,
        "minimum_top_five_overlap": 0.8,
        "safe_error_classes": [],
        "safe_failure_stages": [],
        "attempt_results": attempt_results,
        "checks": {
            "planted_cases": True,
            "material_claim_evidence": True,
            "unsupported_numerical_claims": True,
            "structured_output_success": True,
            "top_five_overlap": True,
        },
        "passed": True,
    }


def _restart_evidence() -> dict[str, object]:
    run_id = "11111111-1111-4111-8111-111111111111"
    common = {
        "run_id": run_id,
        "container_id_before": "a" * 64,
        "container_id_after": "a" * 64,
        "container_started_at_before": "2026-07-15T10:00:00Z",
        "container_started_at_after": "2026-07-15T10:00:05Z",
        "healthy_at": "2026-07-15T10:00:10Z",
        "health_after": "healthy",
    }
    return {
        "schema": "agi-workflow-restart-evidence-v1",
        "status": "passed",
        "workflow_id": "release-growth-diagnostic",
        "run_id": run_id,
        "agent_step": "company_agent",
        "final_run_status": "completed",
        "started_at": "2026-07-15T09:59:00Z",
        "finished_at": "2026-07-15T10:01:00Z",
        "restarts": [
            {
                **common,
                "stage": "agent_execution",
                "run_status_before": "running",
                "step_status_before": "running",
            },
            {
                **common,
                "stage": "approval_wait",
                "container_started_at_before": "2026-07-15T10:00:05Z",
                "container_started_at_after": "2026-07-15T10:00:15Z",
                "healthy_at": "2026-07-15T10:00:20Z",
                "run_status_before": "awaiting_approval",
                "approval_status_before": "pending",
            },
        ],
    }


def test_qualification_report_requires_consistent_twenty_run_gate() -> None:
    summary = validate_qualification_report(
        _qualification_report(), expected_profile="local-strong"
    )
    assert summary == {
        "profile": "local-strong",
        "attempts": 20,
        "successful_runs": 20,
        "success_rate": 1.0,
    }


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda report: report.update(passed=False), "not marked passed"),
        (
            lambda report: report["attempt_results"][0].update(
                unsupported_numerical_claims=1
            ),
            "unsupported material claims",
        ),
        (lambda report: report.update(prompt="sensitive"), "Forbidden content-bearing field"),
        (lambda report: report.update(attempts=19), "greater than or equal to 20"),
    ],
)
def test_qualification_report_rejects_false_or_unsafe_evidence(
    mutation: Any, message: str
) -> None:
    report = _qualification_report()
    mutation(report)
    with pytest.raises(ReleaseEvidenceError, match=message):
        validate_qualification_report(report, expected_profile="local-strong")


def test_restart_evidence_binds_two_restarts_to_one_run_and_container() -> None:
    summary = validate_restart_evidence(
        _restart_evidence(), expected_workflow_id="release-growth-diagnostic"
    )
    assert summary["restart_count"] == 2
    assert summary["run_id"] == "11111111-1111-4111-8111-111111111111"


def test_restart_evidence_rejects_changed_run_or_non_agent_restart() -> None:
    evidence = _restart_evidence()
    evidence["agent_step"] = "normalize"
    with pytest.raises(ReleaseEvidenceError, match="release agent step"):
        validate_restart_evidence(evidence, expected_workflow_id="release-growth-diagnostic")
    evidence = _restart_evidence()
    evidence["restarts"][1]["run_id"] = "22222222-2222-4222-8222-222222222222"
    with pytest.raises(ReleaseEvidenceError, match="same run ID"):
        validate_restart_evidence(evidence, expected_workflow_id="release-growth-diagnostic")


def test_manifest_fails_closed_and_hashes_required_artifacts(tmp_path: Path) -> None:
    steps = tmp_path / "steps.tsv"
    steps.write_text("qualification\tpassed\t4\nrestart\tpassed\t2\n", encoding="utf-8")
    evidence = tmp_path / "qualification.json"
    evidence.write_text(json.dumps(_qualification_report()), encoding="utf-8")
    manifest = build_release_manifest(
        steps_path=steps,
        output_path=tmp_path / "manifest.json",
        started_at="2026-07-15T10:00:00Z",
        exit_code=0,
        git_commit="a" * 40,
        model_profile="local-strong",
        artifacts={"model_qualification": evidence},
    )
    assert manifest["result"] == "passed"
    assert manifest["artifacts"][0]["sha256"]

    steps.write_text("qualification\tfailed\t4\n", encoding="utf-8")
    failed = build_release_manifest(
        steps_path=steps,
        output_path=tmp_path / "failed-manifest.json",
        started_at="2026-07-15T10:00:00Z",
        exit_code=0,
        git_commit="a" * 40,
        model_profile="local-strong",
        artifacts={},
    )
    assert failed["result"] == "failed"


def test_passing_manifest_rejects_missing_or_external_artifacts(tmp_path: Path) -> None:
    steps = tmp_path / "steps.tsv"
    steps.write_text("qualification\tpassed\t1\n", encoding="utf-8")
    with pytest.raises(ReleaseEvidenceError, match="missing"):
        build_release_manifest(
            steps_path=steps,
            output_path=tmp_path / "manifest.json",
            started_at="2026-07-15T10:00:00Z",
            exit_code=0,
            git_commit="a" * 40,
            model_profile="local-strong",
            artifacts={"required": tmp_path / "missing.json"},
        )

    outside = tmp_path.parent / "outside-release-evidence.json"
    outside.write_text("{}", encoding="utf-8")
    try:
        with pytest.raises(ReleaseEvidenceError, match="outside"):
            build_release_manifest(
                steps_path=steps,
                output_path=tmp_path / "manifest.json",
                started_at="2026-07-15T10:00:00Z",
                exit_code=0,
                git_commit="a" * 40,
                model_profile="local-strong",
                artifacts={"outside": outside},
            )
    finally:
        outside.unlink()
