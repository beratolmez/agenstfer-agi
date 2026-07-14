from __future__ import annotations

from copy import deepcopy
from typing import Any

from dbos import DBOS

from agi_server.domain.demo import build_demo_dataset, demo_counts
from agi_server.domain.diagnostic import build_growth_diagnostic
from agi_server.workflow.models import NodeKind, WorkflowDefinition
from agi_server.workflow.validator import validate_workflow


def execute_node_logic(node: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    """Deterministic node dispatcher; DBOS step wrapper checkpoints each return value."""
    result = deepcopy(state)
    kind = NodeKind(node["kind"])
    node_id = str(node["id"])
    if kind in {NodeKind.MANUAL_TRIGGER, NodeKind.ONBOARDING_TRIGGER, NodeKind.SCHEDULE_TRIGGER}:
        result["triggered_by"] = kind.value
    elif kind == NodeKind.DATA_SOURCE_SYNC:
        result["source_counts"] = demo_counts(build_demo_dataset()).model_dump()
        result["connector_id"] = node.get("config", {}).get("connector_id")
    elif kind == NodeKind.NORMALIZE_CONTEXT:
        result["context_status"] = "normalized"
    elif kind == NodeKind.OKF_COMPILE:
        result["knowledge_artifact"] = "okf://bundles/company@candidate"
    elif kind == NodeKind.KNOWLEDGE_SEARCH:
        result["evidence_query"] = node.get("config", {}).get("query")
        result["evidence_sources"] = ["src-crm-001", "src-erp-001", "src-strategy-001"]
    elif kind == NodeKind.AGENT_RUN:
        config = node.get("config", {})
        result.setdefault("agent_results", {})[node_id] = {
            "agent_id": config.get("agent_id"),
            "model_profile": config.get("model_profile"),
            "output_type": config.get("output_type"),
            "status": "simulated-dry-run-no-model-call",
            "executed": False,
        }
    elif kind == NodeKind.DETERMINISTIC_SCORE:
        diagnostic = build_growth_diagnostic()
        result["diagnostic"] = diagnostic.model_dump(mode="json")
    elif kind in {NodeKind.CONDITION, NodeKind.POLICY_CHECK}:
        result.setdefault("policy_checks", {})[node_id] = "passed"
    elif kind == NodeKind.REPORT_OUTPUT:
        result["artifact_uri"] = "okf://reports/growth-diagnostic-v1"
        result["format"] = node.get("config", {}).get("format", "okf+html")
    result["last_step"] = node_id
    return result


@DBOS.step(name="agi.execute_workflow_node", retries_allowed=True, max_attempts=3)
def execute_node_step(node: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    return execute_node_logic(node, state)


@DBOS.workflow(name="agi.versioned_workflow_interpreter")
def durable_workflow_interpreter(
    workflow_payload: dict[str, Any], initial_context: dict[str, Any]
) -> dict[str, Any]:
    workflow = WorkflowDefinition.model_validate(workflow_payload)
    validation = validate_workflow(workflow)
    if not validation.valid:
        raise ValueError(f"Invalid workflow: {[issue.code for issue in validation.issues]}")
    nodes = {node.id: node for node in workflow.nodes}
    state = deepcopy(initial_context)
    state.update({"workflow_id": workflow.id, "workflow_version": workflow.version})
    for node_id in validation.topological_order:
        node = nodes[node_id]
        if node.kind == NodeKind.APPROVAL:
            if state.get("dry_run"):
                state["approval"] = {"status": "skipped-in-dry-run", "node_id": node_id}
            else:
                timeout_days = int(node.config.get("timeout_days", 7))
                decision = DBOS.recv(
                    topic=f"approval:{node_id}", timeout_seconds=timeout_days * 24 * 60 * 60
                )
                if not isinstance(decision, dict) or decision.get("decision") != "approved":
                    return {
                        **state,
                        "approval": decision or {"decision": "expired"},
                        "status": "rejected",
                    }
                state["approval"] = decision
                state["last_step"] = node_id
        else:
            state = execute_node_step(node.model_dump(mode="json"), state)
    return {**state, "status": "completed"}


def run_workflow_locally(
    workflow: WorkflowDefinition, initial_context: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Non-durable dry-run path used by local tests and the visual editor."""
    validation = validate_workflow(workflow)
    if not validation.valid:
        raise ValueError([issue.model_dump() for issue in validation.issues])
    nodes = {node.id: node for node in workflow.nodes}
    state = {**(initial_context or {}), "dry_run": True}
    for node_id in validation.topological_order:
        node = nodes[node_id]
        if node.kind == NodeKind.APPROVAL:
            state["approval"] = {"status": "skipped-in-dry-run", "node_id": node_id}
        else:
            state = execute_node_logic(node.model_dump(mode="json"), state)
    return {**state, "status": "dry-run-completed"}
