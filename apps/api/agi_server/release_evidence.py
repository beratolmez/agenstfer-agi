from __future__ import annotations

import hashlib
import json
import math
import platform
import re
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from agi_server.agents.model_gateway import CONTROL_PLANE_POLICY_REVISION


class ReleaseEvidenceError(ValueError):
    """Raised when release evidence is incomplete, inconsistent, or unsafe to retain."""


REQUIRED_QUALIFICATION_CHECKS = {
    "planted_cases",
    "material_claim_evidence",
    "unsupported_numerical_claims",
    "structured_output_success",
    "top_five_overlap",
}
AGENT_RESTART_STEPS = {"company_agent", "growth_agent", "review", "curator"}
FORBIDDEN_EVIDENCE_KEYS = {
    "api_key",
    "bootstrap_token",
    "cloud_api_key",
    "credential",
    "credentials",
    "evidence_excerpt",
    "evidence_excerpts",
    "password",
    "prompt",
    "prompts",
    "raw_content",
    "secret",
    "secrets",
    "session_token",
    "source_body",
    "source_bodies",
    "source_content",
}


def load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ReleaseEvidenceError(f"Could not read JSON evidence: {path.name}") from error
    if not isinstance(value, dict):
        raise ReleaseEvidenceError(f"JSON evidence must be an object: {path.name}")
    return value


def _assert_content_safe(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in FORBIDDEN_EVIDENCE_KEYS or normalized.endswith("_api_key"):
                raise ReleaseEvidenceError(f"Forbidden content-bearing field at {path}.{key}")
            _assert_content_safe(child, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _assert_content_safe(child, f"{path}[{index}]")


def _integer(value: Any, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ReleaseEvidenceError(f"{label} must be an integer greater than or equal to {minimum}")
    return value


def _number(value: Any, label: str, *, minimum: float = 0.0, maximum: float = 1.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ReleaseEvidenceError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result) or result < minimum or result > maximum:
        raise ReleaseEvidenceError(f"{label} must be between {minimum} and {maximum}")
    return result


def _timestamp(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ReleaseEvidenceError(f"{label} must be a timestamp")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ReleaseEvidenceError(f"{label} must be an ISO-8601 timestamp") from error
    return value


def _parsed_timestamp(value: Any, label: str) -> datetime:
    parsed = datetime.fromisoformat(_timestamp(value, label).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ReleaseEvidenceError(f"{label} must include a timezone")
    return parsed


def validate_qualification_report(
    report: Mapping[str, Any],
    *,
    expected_profile: str,
    minimum_attempts: int = 20,
) -> dict[str, Any]:
    """Validate model qualification independently from the evaluator process exit code."""
    _assert_content_safe(report)
    if report.get("profile") != expected_profile:
        raise ReleaseEvidenceError("Qualification profile does not match the release profile")
    attempts = _integer(report.get("attempts"), "attempts", minimum=minimum_attempts)
    successful_runs = _integer(report.get("successful_runs"), "successful_runs")
    if successful_runs > attempts:
        raise ReleaseEvidenceError("successful_runs cannot exceed attempts")
    success_rate = _number(report.get("success_rate"), "success_rate")
    if not math.isclose(success_rate, successful_runs / attempts, abs_tol=1e-9):
        raise ReleaseEvidenceError("success_rate is inconsistent with successful_runs")
    if successful_runs < math.ceil(attempts * 0.95):
        raise ReleaseEvidenceError("Structured-output success is below 95 percent")

    checks = report.get("checks")
    if not isinstance(checks, Mapping):
        raise ReleaseEvidenceError("Qualification checks are missing")
    if not REQUIRED_QUALIFICATION_CHECKS.issubset(checks):
        raise ReleaseEvidenceError("Qualification checks are incomplete")
    if any(value is not True for value in checks.values()):
        raise ReleaseEvidenceError("Every qualification check must pass")
    if report.get("passed") is not True:
        raise ReleaseEvidenceError("Qualification report is not marked passed")

    if _integer(report.get("minimum_planted_cases"), "minimum_planted_cases") < 5:
        raise ReleaseEvidenceError("Fewer than five planted opportunities were detected")
    if _integer(report.get("minimum_evidence_coverage"), "minimum_evidence_coverage") != 100:
        raise ReleaseEvidenceError("Material-claim evidence coverage must be 100 percent")
    if _number(report.get("minimum_top_five_overlap"), "minimum_top_five_overlap") < 0.70:
        raise ReleaseEvidenceError("Top-five overlap is below 70 percent")

    attempt_results = report.get("attempt_results")
    if not isinstance(attempt_results, list) or len(attempt_results) != attempts:
        raise ReleaseEvidenceError("attempt_results must contain exactly one record per attempt")
    seen_attempts: set[int] = set()
    passed_attempts = 0
    for item in attempt_results:
        if not isinstance(item, Mapping):
            raise ReleaseEvidenceError("Each attempt result must be an object")
        attempt = _integer(item.get("attempt"), "attempt_results.attempt", minimum=1)
        if attempt in seen_attempts or attempt > attempts:
            raise ReleaseEvidenceError("Attempt numbers must be unique and in range")
        seen_attempts.add(attempt)
        status = item.get("status")
        if status == "passed":
            passed_attempts += 1
            material = _integer(item.get("material_claim_count"), "material_claim_count")
            supported = _integer(item.get("supported_claim_count"), "supported_claim_count")
            unsupported = _integer(
                item.get("unsupported_numerical_claims"),
                "unsupported_numerical_claims",
            )
            if material != supported or unsupported != 0:
                raise ReleaseEvidenceError("A passed attempt contains unsupported material claims")
        elif status != "failed":
            raise ReleaseEvidenceError("Attempt status must be passed or failed")
    if seen_attempts != set(range(1, attempts + 1)) or passed_attempts != successful_runs:
        raise ReleaseEvidenceError("Attempt records are inconsistent with successful_runs")

    failures = attempts - successful_runs
    safe_errors = report.get("safe_error_classes")
    failure_stages = report.get("safe_failure_stages")
    if not isinstance(safe_errors, list) or len(safe_errors) != failures:
        raise ReleaseEvidenceError("safe_error_classes is inconsistent with failed attempts")
    if not isinstance(failure_stages, list) or len(failure_stages) != failures:
        raise ReleaseEvidenceError("safe_failure_stages is inconsistent with failed attempts")
    if not isinstance(report.get("provider"), str) or not report["provider"]:
        raise ReleaseEvidenceError("Qualified provider identity is missing")
    if not isinstance(report.get("model"), str) or not report["model"]:
        raise ReleaseEvidenceError("Qualified model identity is missing")

    if report.get("qualification_path") != "published-persistent-workflow-v1":
        raise ReleaseEvidenceError("Qualification did not exercise the published workflow path")
    retrieval_revisions = report.get("retrieval_revisions")
    if not isinstance(retrieval_revisions, list) or len(retrieval_revisions) != attempts:
        raise ReleaseEvidenceError("Qualification retrieval revisions are incomplete")
    if any(
        not isinstance(revision, str) or re.fullmatch(r"[0-9a-f]{40,64}", revision) is None
        for revision in retrieval_revisions
    ):
        raise ReleaseEvidenceError("Qualification retrieval revision is invalid")
    workflow = report.get("workflow")
    expected_workflow_id = f"qualification-{expected_profile}"
    if not isinstance(workflow, Mapping) or workflow.get("id") != expected_workflow_id:
        raise ReleaseEvidenceError("Qualification workflow identity is missing")
    _integer(workflow.get("version"), "workflow.version", minimum=1)
    workflow_digest = report.get("workflow_definition_sha256")
    valid_workflow_digest = isinstance(workflow_digest, str) and re.fullmatch(
        r"[0-9a-f]{64}", workflow_digest
    )
    if not valid_workflow_digest:
        raise ReleaseEvidenceError("Qualification workflow definition hash is invalid")
    agent_versions = report.get("agent_versions")
    agent_profiles = report.get("agent_model_profiles")
    prompt_hashes = report.get("effective_prompt_sha256")
    required_agents = {
        "company-analyst",
        "growth-opportunity-analyst",
        "evidence-reviewer",
        "wiki-curator",
    }
    if not isinstance(agent_versions, Mapping) or set(agent_versions) != required_agents:
        raise ReleaseEvidenceError("Qualification agent-version bindings are incomplete")
    if not isinstance(agent_profiles, Mapping) or set(agent_profiles) != required_agents:
        raise ReleaseEvidenceError("Qualification agent-profile bindings are incomplete")
    if not isinstance(prompt_hashes, Mapping) or set(prompt_hashes) != required_agents:
        raise ReleaseEvidenceError("Qualification effective-prompt hashes are incomplete")
    for agent_id in required_agents:
        _integer(agent_versions[agent_id], f"agent_versions.{agent_id}", minimum=1)
        if agent_profiles[agent_id] != expected_profile:
            raise ReleaseEvidenceError("Qualification agent profile does not match release profile")
        digest = prompt_hashes[agent_id]
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ReleaseEvidenceError("Qualification effective-prompt hash is invalid")
    policy_revision = report.get("control_plane_policy_revision")
    if not isinstance(policy_revision, str) or not policy_revision:
        raise ReleaseEvidenceError("Control-plane policy revision is missing")
    if policy_revision != CONTROL_PLANE_POLICY_REVISION:
        raise ReleaseEvidenceError("Qualification control-plane policy revision is stale")

    return {
        "profile": expected_profile,
        "attempts": attempts,
        "successful_runs": successful_runs,
        "success_rate": success_rate,
        "control_plane_policy_revision": policy_revision,
    }


def validate_restart_evidence(
    evidence: Mapping[str, Any],
    *,
    expected_workflow_id: str,
) -> dict[str, Any]:
    """Validate that one persisted run survived agent and approval-wait restarts."""
    _assert_content_safe(evidence)
    if evidence.get("schema") != "agi-workflow-restart-evidence-v1":
        raise ReleaseEvidenceError("Unsupported restart evidence schema")
    if evidence.get("status") != "passed":
        raise ReleaseEvidenceError("Restart evidence is not marked passed")
    if evidence.get("workflow_id") != expected_workflow_id:
        raise ReleaseEvidenceError("Restart evidence workflow does not match")
    run_id = evidence.get("run_id")
    try:
        parsed_run_id = UUID(str(run_id))
    except (ValueError, TypeError, AttributeError) as error:
        raise ReleaseEvidenceError("Restart evidence run ID is invalid") from error
    if str(parsed_run_id) != run_id:
        raise ReleaseEvidenceError("Restart evidence run ID is invalid")
    if evidence.get("agent_step") not in AGENT_RESTART_STEPS:
        raise ReleaseEvidenceError("Restart was not observed during a release agent step")
    if evidence.get("final_run_status") != "completed":
        raise ReleaseEvidenceError("The restarted workflow did not complete")
    started_at = _parsed_timestamp(evidence.get("started_at"), "started_at")
    finished_at = _parsed_timestamp(evidence.get("finished_at"), "finished_at")
    if finished_at < started_at:
        raise ReleaseEvidenceError("Restart evidence finished before it started")

    restarts = evidence.get("restarts")
    if not isinstance(restarts, list) or len(restarts) != 2:
        raise ReleaseEvidenceError("Exactly two restart records are required")
    expected_stages = ["agent_execution", "approval_wait"]
    app_container_id: str | None = None
    for index, item in enumerate(restarts):
        if not isinstance(item, Mapping) or item.get("stage") != expected_stages[index]:
            raise ReleaseEvidenceError("Restart stages are missing or out of order")
        if item.get("run_id") != run_id:
            raise ReleaseEvidenceError("Restart records must retain the same run ID")
        before_id = item.get("container_id_before")
        after_id = item.get("container_id_after")
        if (
            not isinstance(before_id, str)
            or not re.fullmatch(r"[0-9a-f]{64}", before_id)
            or before_id != after_id
        ):
            raise ReleaseEvidenceError("App restart must preserve the same container ID")
        if app_container_id is None:
            app_container_id = before_id
        elif before_id != app_container_id:
            raise ReleaseEvidenceError("Both restarts must target the same app container")
        before_started = _parsed_timestamp(
            item.get("container_started_at_before"), "restart.started_before"
        )
        after_started = _parsed_timestamp(
            item.get("container_started_at_after"), "restart.started_after"
        )
        healthy_at = _parsed_timestamp(item.get("healthy_at"), "restart.healthy_at")
        if after_started <= before_started:
            raise ReleaseEvidenceError("Container start time did not advance across restart")
        if healthy_at < after_started:
            raise ReleaseEvidenceError("Healthy checkpoint predates the restarted container")
        if item.get("health_after") != "healthy":
            raise ReleaseEvidenceError("App was not healthy after restart")

    first, second = restarts
    if first.get("run_status_before") != "running" or first.get("step_status_before") != "running":
        raise ReleaseEvidenceError("First restart was not captured during active agent execution")
    if second.get("run_status_before") != "awaiting_approval":
        raise ReleaseEvidenceError("Second restart was not captured during approval wait")
    if second.get("approval_status_before") != "pending":
        raise ReleaseEvidenceError("Approval was not pending before the approval-wait restart")

    return {"workflow_id": expected_workflow_id, "run_id": run_id, "restart_count": 2}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_release_manifest(
    *,
    steps_path: Path,
    output_path: Path,
    started_at: str,
    exit_code: int,
    git_commit: str,
    model_profile: str,
    artifacts: Mapping[str, Path],
) -> dict[str, Any]:
    """Build a content-safe, hash-bound release manifest from verified step evidence."""
    _timestamp(started_at, "started_at")
    steps: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    try:
        lines = steps_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise ReleaseEvidenceError("Could not read rehearsal steps") from error
    for line in lines:
        parts = line.split("\t")
        if len(parts) != 3:
            raise ReleaseEvidenceError("Malformed rehearsal step record")
        name, status, duration_text = parts
        if not name or name in seen_names or status not in {"passed", "failed"}:
            raise ReleaseEvidenceError("Invalid or duplicate rehearsal step")
        seen_names.add(name)
        try:
            duration = int(duration_text)
        except ValueError as error:
            raise ReleaseEvidenceError("Step duration must be an integer") from error
        if duration < 0:
            raise ReleaseEvidenceError("Step duration cannot be negative")
        steps.append({"name": name, "status": status, "duration_seconds": duration})

    passed = exit_code == 0 and bool(steps) and all(item["status"] == "passed" for item in steps)
    root = output_path.parent.resolve()
    artifact_records: list[dict[str, Any]] = []
    for name, path in artifacts.items():
        if not path.exists():
            if passed:
                raise ReleaseEvidenceError(f"Required release artifact is missing: {name}")
            continue
        if path.is_symlink() or not path.is_file():
            raise ReleaseEvidenceError(f"Release artifact must be a regular file: {name}")
        resolved = path.resolve()
        try:
            relative = resolved.relative_to(root)
        except ValueError as error:
            raise ReleaseEvidenceError(
                f"Release artifact is outside the evidence directory: {name}"
            ) from error
        artifact_records.append(
            {
                "name": name,
                "path": relative.as_posix(),
                "sha256": _sha256(resolved),
                "size_bytes": resolved.stat().st_size,
            }
        )

    payload = {
        "schema": "agi-release-rehearsal-v2",
        "started_at": started_at,
        "finished_at": datetime.now().astimezone().isoformat(),
        "result": "passed" if passed else "failed",
        "exit_code": exit_code,
        "git_commit": git_commit,
        "host": {"system": platform.system(), "machine": platform.machine()},
        "model_profile": model_profile,
        "steps": steps,
        "artifacts": artifact_records,
        "content_policy": (
            "No prompts, source bodies, evidence excerpts, credentials, or provider keys."
        ),
    }
    _assert_content_safe(payload)
    return payload
