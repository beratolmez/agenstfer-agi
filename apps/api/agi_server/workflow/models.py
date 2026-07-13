from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class NodeKind(StrEnum):
    MANUAL_TRIGGER = "manual_trigger"
    ONBOARDING_TRIGGER = "onboarding_trigger"
    SCHEDULE_TRIGGER = "schedule_trigger"
    DATA_SOURCE_SYNC = "data_source_sync"
    NORMALIZE_CONTEXT = "normalize_context"
    OKF_COMPILE = "okf_compile"
    KNOWLEDGE_SEARCH = "knowledge_search"
    AGENT_RUN = "agent_run"
    DETERMINISTIC_SCORE = "deterministic_score"
    CONDITION = "condition"
    POLICY_CHECK = "policy_check"
    APPROVAL = "approval"
    REPORT_OUTPUT = "report_output"


class WorkflowNode(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{1,63}$")
    kind: NodeKind
    label: str = Field(min_length=1, max_length=100)
    position: dict[str, float] = Field(default_factory=lambda: {"x": 0, "y": 0})
    config: dict[str, Any] = Field(default_factory=dict)
    output_type: str | None = None


class WorkflowEdge(BaseModel):
    id: str
    source: str
    target: str
    data_type: str = "control"


class WorkflowDefinition(BaseModel):
    id: str
    name: str
    version: int = Field(ge=1)
    status: str = "draft"
    nodes: list[WorkflowNode]
    edges: list[WorkflowEdge]

    @model_validator(mode="after")
    def unique_ids(self) -> WorkflowDefinition:
        node_ids = [node.id for node in self.nodes]
        edge_ids = [edge.id for edge in self.edges]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("Workflow node ID'leri benzersiz olmalıdır")
        if len(edge_ids) != len(set(edge_ids)):
            raise ValueError("Workflow edge ID'leri benzersiz olmalıdır")
        return self


class WorkflowIssue(BaseModel):
    code: str
    message: str
    node_id: str | None = None
    edge_id: str | None = None


class WorkflowValidation(BaseModel):
    valid: bool
    issues: list[WorkflowIssue]
    topological_order: list[str] = Field(default_factory=list)
