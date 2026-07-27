from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy.orm import Session

from agi_server.agents.contracts import (
    CompanyAnalysis,
    EvidenceReview,
    OpportunityHypotheses,
)
from agi_server.agents.model_gateway import (
    CONTROL_PLANE_POLICY_REVISION,
    effective_system_prompt,
)
from agi_server.config import Settings
from agi_server.db import AgentDefinitionRow, WorkflowDefinitionRow, WorkflowRun
from agi_server.schemas import GrowthDiagnostic
from agi_server.workflow.default import build_default_workflow
from agi_server.workflow.models import NodeKind
from agi_server.workflow.registry_service import (
    agent_from_row,
    clone_workflow_version,
    ensure_platform_registry,
    publish_workflow,
    save_workflow_draft,
    workflow_from_row,
)

QUALIFICATION_PATH = "published-persistent-workflow-v1"


def prepare_qualification_workflow(
    db: Session, profile_id: str, settings: Settings | None = None
) -> WorkflowDefinitionRow:
    """Create the exact immutable workflow version exercised by a qualification attempt."""
    ensure_platform_registry(db)
    default = build_default_workflow()
    source = db.get(WorkflowDefinitionRow, (default.id, default.version))
    if source is None or source.status != "published":
        raise RuntimeError("Published built-in qualification workflow is unavailable")
    draft = clone_workflow_version(
        db,
        source,
        actor_id=None,
        target_id=f"qualification-{profile_id}",
    )
    definition = workflow_from_row(draft)
    definition.name = f"Qualification: {profile_id}"
    for node in definition.nodes:
        if node.kind == NodeKind.AGENT_RUN:
            node.config["model_profile"] = profile_id
    save_workflow_draft(db, definition, actor_id=None)
    return publish_workflow(db, draft, settings=settings)


def summarize_qualification_run(run: WorkflowRun) -> dict[str, Any]:
    """Extract release metrics only from the persisted production workflow result."""
    if run.status not in {"awaiting_approval", "completed"}:
        raise RuntimeError("Qualification workflow did not reach an evidence-reviewed report")
    output = run.output_json or {}
    agent_results = output.get("agent_results")
    if not isinstance(agent_results, dict):
        raise RuntimeError("Qualification workflow has no persisted agent results")
    diagnostic = GrowthDiagnostic.model_validate(output.get("diagnostic"))
    company = CompanyAnalysis.model_validate(agent_results.get("company-analyst"))
    hypotheses = OpportunityHypotheses.model_validate(
        agent_results.get("growth-opportunity-analyst")
    )
    review = EvidenceReview.model_validate(agent_results.get("evidence-reviewer"))
    expected_claims = (
        len(company.strengths)
        + len(company.weaknesses)
        + len(hypotheses.hypotheses)
        + len(diagnostic.opportunities)
    )
    supported = [item for item in review.decisions if item.supported]
    numerical_ids = {f"metric-{item.id}" for item in diagnostic.opportunities}
    supported_ids = {item.claim_id for item in supported}
    return {
        "diagnostic": diagnostic,
        "material_claim_count": expected_claims,
        "supported_claim_count": len(supported),
        "evidence_coverage": round(100 * len(supported) / max(1, expected_claims)),
        "unsupported_numerical_claims": len(numerical_ids - supported_ids),
    }


def qualification_provenance(
    db: Session,
    workflow: WorkflowDefinitionRow,
) -> dict[str, Any]:
    """Return content-safe hashes binding a report to workflow, agents, and effective policy."""
    definition = workflow_from_row(workflow)
    agent_versions: dict[str, int] = {}
    agent_model_profiles: dict[str, str] = {}
    prompt_hashes: dict[str, str] = {}
    for node in definition.nodes:
        if node.kind != NodeKind.AGENT_RUN:
            continue
        agent_id = str(node.config["agent_id"])
        version = int(node.config["agent_version"])
        row = db.get(AgentDefinitionRow, (agent_id, version))
        if row is None or row.status != "published":
            raise RuntimeError(f"Pinned agent is unavailable: {agent_id}:{version}")
        spec = agent_from_row(row)
        agent_versions[agent_id] = version
        agent_model_profiles[agent_id] = str(node.config["model_profile"])
        prompt_hashes[agent_id] = hashlib.sha256(
            effective_system_prompt(spec.system_prompt).encode("utf-8")
        ).hexdigest()
    return {
        "qualification_path": QUALIFICATION_PATH,
        "workflow": {"id": workflow.id, "version": workflow.version},
        "workflow_definition_sha256": hashlib.sha256(
            json.dumps(
                definition.model_dump(mode="json"),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest(),
        "agent_versions": agent_versions,
        "agent_model_profiles": agent_model_profiles,
        "effective_prompt_sha256": prompt_hashes,
        "control_plane_policy_revision": CONTROL_PLANE_POLICY_REVISION,
    }
