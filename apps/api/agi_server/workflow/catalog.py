from __future__ import annotations

from dataclasses import dataclass

from agi_server.workflow.models import NodeKind


@dataclass(frozen=True)
class NodeSpec:
    label: str
    group: str
    accepted_inputs: frozenset[str]
    default_output: str
    required_config: frozenset[str] = frozenset()
    risk: str = "low"


NODE_CATALOG: dict[NodeKind, NodeSpec] = {
    NodeKind.MANUAL_TRIGGER: NodeSpec("Manual Trigger", "Trigger", frozenset(), "control"),
    NodeKind.ONBOARDING_TRIGGER: NodeSpec("Onboarding Trigger", "Trigger", frozenset(), "control"),
    NodeKind.SCHEDULE_TRIGGER: NodeSpec(
        "Schedule Trigger", "Trigger", frozenset(), "control", frozenset({"cron"})
    ),
    NodeKind.DATA_SOURCE_SYNC: NodeSpec(
        "Data Source Sync",
        "Veri",
        frozenset({"control"}),
        "raw_records",
        frozenset({"connector_id"}),
    ),
    NodeKind.NORMALIZE_CONTEXT: NodeSpec(
        "Normalize Context", "Veri", frozenset({"raw_records"}), "context"
    ),
    NodeKind.OKF_COMPILE: NodeSpec(
        "OKF Compile", "AI ve Analiz", frozenset({"context"}), "knowledge"
    ),
    NodeKind.KNOWLEDGE_SEARCH: NodeSpec(
        "Knowledge Search",
        "AI ve Analiz",
        frozenset({"knowledge", "context"}),
        "evidence",
        frozenset({"query"}),
    ),
    NodeKind.AGENT_RUN: NodeSpec(
        "Agent Run",
        "AI ve Analiz",
        frozenset(
            {
                "knowledge",
                "context",
                "evidence",
                "hypotheses",
                "scored_opportunities",
                "agent_result",
            }
        ),
        "agent_result",
        frozenset({"agent_id", "model_profile"}),
    ),
    NodeKind.DETERMINISTIC_SCORE: NodeSpec(
        "Deterministic Score",
        "AI ve Analiz",
        frozenset({"hypotheses", "agent_result"}),
        "scored_opportunities",
    ),
    NodeKind.CONDITION: NodeSpec(
        "Condition",
        "Kontrol",
        frozenset({"control", "agent_result", "scored_opportunities"}),
        "control",
        frozenset({"field", "operator", "value"}),
    ),
    NodeKind.POLICY_CHECK: NodeSpec(
        "Policy Check",
        "Kontrol",
        frozenset({"control", "agent_result", "scored_opportunities"}),
        "control",
        frozenset({"policy_id"}),
    ),
    NodeKind.APPROVAL: NodeSpec(
        "Approval",
        "Kontrol",
        frozenset({"control", "agent_result", "scored_opportunities", "artifact"}),
        "approved",
        frozenset({"role", "timeout_days"}),
        risk="medium",
    ),
    NodeKind.REPORT_OUTPUT: NodeSpec(
        "Report Output",
        "Çıktı",
        frozenset({"approved", "control", "scored_opportunities", "agent_result"}),
        "artifact",
        frozenset({"format"}),
    ),
}
