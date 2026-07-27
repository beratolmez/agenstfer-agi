from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from typing import Any, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy import select
from sqlalchemy.orm import Session

from agi_server.config import Settings
from agi_server.db import (
    ApprovalRequest,
    OKFCandidate,
    WorkflowRun,
    WorkflowStepRun,
    utcnow,
)
from agi_server.logging_utils import build_error_details, logger
from agi_server.workflow.models import NodeKind, WorkflowDefinition
from agi_server.workflow.validator import validate_workflow


class LangGraphWorkflowState(TypedDict, total=False):
    run_id: str
    workflow_id: str
    workflow_version: int
    status: str
    current_node: str | None
    state_data: dict[str, Any]
    execution_context: dict[str, Any]
    step_history: list[str]
    error: str | None


GrowthWorkflowState = LangGraphWorkflowState


class LangGraphWorkflowEngine:
    """LangGraph StateGraph execution engine for B2B growth diagnostic workflows."""

    def __init__(
        self,
        db: Session,
        settings: Settings,
        run: WorkflowRun,
        workflow: WorkflowDefinition,
        *,
        model_overrides: dict[str, Any] | None = None,
    ) -> None:
        self.db = db
        self.settings = settings
        self.run = run
        self.workflow = workflow
        self.model_overrides = model_overrides
        self.validation = validate_workflow(workflow)
        if not self.validation.valid:
            raise ValueError([item.model_dump() for item in self.validation.issues])

        self.nodes = {node.id: node for node in workflow.nodes}
        self.incoming = {node.id: [] for node in workflow.nodes}
        self.outgoing = {node.id: [] for node in workflow.nodes}
        for edge in workflow.edges:
            self.incoming[edge.target].append(edge)
            self.outgoing[edge.source].append(edge)

        self.graph = self._build_graph()

    def _build_graph(self) -> CompiledStateGraph:
        builder = StateGraph(LangGraphWorkflowState)

        topological_order = self.validation.topological_order
        for sequence, node_id in enumerate(topological_order, start=1):
            builder.add_node(node_id, self._make_node_executor(node_id, sequence))

        if topological_order:
            builder.add_edge(START, topological_order[0])
            for i in range(len(topological_order) - 1):
                builder.add_edge(topological_order[i], topological_order[i + 1])
            builder.add_edge(topological_order[-1], END)

        checkpointer = MemorySaver()
        return builder.compile(checkpointer=checkpointer)

    def _make_node_executor(self, node_id: str, sequence: int):
        from agi_server.workflow.persistent_runtime import (
            _aggregate_usage,
            _execute_node,
            _step,
        )

        async def _node_executor(state: LangGraphWorkflowState) -> LangGraphWorkflowState:
            if state.get("status") in {"awaiting_approval", "failed"}:
                return state

            try:
                node = self.nodes[node_id]
                state_data = deepcopy(state.get("state_data", {}))
                active_edges = set(state_data.get("_active_edges", []))

                completed_steps = {
                    item.sequence: item
                    for item in self.db.scalars(
                        select(WorkflowStepRun).where(WorkflowStepRun.run_id == self.run.id)
                    )
                }
                prior = completed_steps.get(sequence)
                if prior is not None and prior.status in {"completed", "skipped"}:
                    return state

                is_trigger = node.kind in {
                    NodeKind.MANUAL_TRIGGER,
                    NodeKind.ONBOARDING_TRIGGER,
                    NodeKind.SCHEDULE_TRIGGER,
                }
                active = is_trigger or any(
                    edge.id in active_edges for edge in self.incoming[node_id]
                )
                step = prior or _step(self.db, self.run, node, sequence, state_data)
                self.run.current_step = node.id

                if not active:
                    step.status = "skipped"
                    step.completed_at = utcnow()
                    self.db.commit()
                    return state

                if node.kind == NodeKind.APPROVAL:
                    if step.status == "awaiting_approval":
                        self.run.status = "awaiting_approval"
                        state["status"] = "awaiting_approval"
                        return state
                    candidate_id = state_data.get("candidate_id")
                    if not candidate_id or self.db.get(OKFCandidate, candidate_id) is None:
                        raise ValueError("Approval requires a persisted OKF candidate")
                    approval = ApprovalRequest(
                        run_id=self.run.id,
                        kind="okf-candidate-merge",
                        status="pending",
                        artifact_uri=self.run.artifact_uri or "",
                        requested_role=str(node.config.get("role", "approver")),
                        candidate_id=candidate_id,
                        expires_at=datetime.now(UTC)
                        + timedelta(days=int(node.config.get("timeout_days", 7))),
                    )
                    self.db.add(approval)
                    step.status = "awaiting_approval"
                    step.output_json = {"approval_id": approval.id, "candidate_id": candidate_id}
                    self.run.status = "awaiting_approval"
                    state_data["_active_edges"] = sorted(active_edges)
                    self.run.output_json = state_data
                    _aggregate_usage(self.db, self.run)
                    self.db.commit()
                    state["status"] = "awaiting_approval"
                    state["state_data"] = state_data
                    return state

                before_state = deepcopy(state_data)
                state_data = await _execute_node(
                    self.db,
                    self.settings,
                    self.run,
                    node,
                    state_data,
                    step,
                    model_overrides=self.model_overrides,
                )
            except Exception as error:
                node_profile = str(
                    node.config.get("model_profile") or self.run.model_profile or ""
                )
                logger.exception(
                    "LangGraph node execution failed for run %s at node %s",
                    self.run.id,
                    node_id,
                )
                error_details = build_error_details(
                    error,
                    settings=self.settings,
                    profile_id=node_profile,
                    node_id=node_id,
                )
                self.run.status = "failed"
                self.run.error_json = error_details
                self.run.completed_at = utcnow()
                if 'step' in locals() and step is not None:
                    step.status = "failed"
                    step.error_json = error_details
                    step.completed_at = utcnow()
                self.db.commit()
                state["status"] = "failed"
                state["error"] = error_details["message"]
                raise error

            if node.kind == NodeKind.CONDITION:
                branch = "true" if state_data["conditions"][node.id] else "false"
                active_edges.update(
                    edge.id for edge in self.outgoing[node.id] if edge.branch == branch
                )
            else:
                active_edges.update(edge.id for edge in self.outgoing[node.id])

            state_data["_active_edges"] = sorted(active_edges)
            step.status = "completed"
            step.output_json = {
                key: value
                for key, value in state_data.items()
                if not key.startswith("_") and before_state.get(key) != value
            }
            step.completed_at = utcnow()
            self.run.output_json = state_data
            self.db.commit()

            history = list(state.get("step_history", []))
            history.append(node.id)
            state["step_history"] = history
            state["state_data"] = state_data
            return state

        return _node_executor

    async def execute_workflow(self) -> WorkflowRun:
        from agi_server.agents.runtime import classify_model_data_scope
        from agi_server.context import ExecutionContext
        from agi_server.workflow.persistent_runtime import _aggregate_usage

        try:
            state_data = deepcopy(
                self.run.output_json or {"_active_edges": [], "input": self.run.input_json or {}}
            )
            data_classification = classify_model_data_scope(self.db)
            exec_ctx = ExecutionContext(
                run_id=self.run.id,
                workflow_id=self.workflow.id,
                workflow_version=self.workflow.version,
                actor_id=self.run.created_by,
                data_classification=data_classification,
                bounded_evidence_ids=list(state_data.get("evidence_ids", [])),
                model_policy_revision=self.run.model_profile or "v1",
            )

            initial_state: LangGraphWorkflowState = {
                "run_id": self.run.id,
                "workflow_id": self.workflow.id,
                "workflow_version": self.workflow.version,
                "status": self.run.status,
                "current_node": None,
                "state_data": state_data,
                "execution_context": exec_ctx.model_dump(mode="json"),
                "step_history": [],
            }

            final_state = await self.graph.ainvoke(initial_state)

            if final_state.get("status") == "awaiting_approval":
                self.run.status = "awaiting_approval"
                _aggregate_usage(self.db, self.run)
                self.db.commit()
                return self.run

            if final_state.get("status") == "failed":
                return self.run

            self.run.status = "completed"
            self.run.current_step = None
            self.run.completed_at = utcnow()
            self.run.output_json = final_state.get("state_data", {})
            _aggregate_usage(self.db, self.run)
            self.db.commit()
            return self.run
        except Exception as exc:
            error_details = build_error_details(
                exc,
                settings=self.settings,
                profile_id=self.run.model_profile,
                node_id=self.run.current_step,
            )
            self.run.status = "failed"
            self.run.error_json = error_details
            self.run.completed_at = utcnow()
            _aggregate_usage(self.db, self.run)
            self.db.commit()
            raise


def build_langgraph_workflow(
    definition: WorkflowDefinition | None = None,
) -> CompiledStateGraph:
    """Builds a compiled LangGraph StateGraph workflow foundation for the given definition."""
    from agi_server.workflow.default import build_default_workflow

    wf = definition or build_default_workflow()
    builder = StateGraph(LangGraphWorkflowState)
    validation = validate_workflow(wf)
    order = validation.topological_order

    for node_id in order:

        def _stub_node(
            state: LangGraphWorkflowState, n_id: str = node_id
        ) -> LangGraphWorkflowState:
            history = list(state.get("step_history", []))
            history.append(n_id)
            new_status = "completed" if n_id == "report" else state.get("status", "running")
            return {**state, "status": new_status, "step_history": history}

        builder.add_node(node_id, _stub_node)

    if order:
        builder.add_edge(START, order[0])
        for i in range(len(order) - 1):
            builder.add_edge(order[i], order[i + 1])
        builder.add_edge(order[-1], END)

    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)


class LangGraphWorkflowRuntime:
    """Foundation runtime seam for compiling and executing LangGraph workflows."""

    def __init__(self, definition: WorkflowDefinition | None = None) -> None:
        from agi_server.workflow.default import build_default_workflow

        self.definition = definition or build_default_workflow()
        self.graph = build_langgraph_workflow(self.definition)

    def execute(
        self, initial_state: LangGraphWorkflowState | None = None
    ) -> LangGraphWorkflowState:
        state: LangGraphWorkflowState = initial_state or {
            "workflow_id": self.definition.id,
            "status": "pending",
            "state_data": {},
            "step_history": [],
        }
        output = self.graph.invoke(state)
        return output
