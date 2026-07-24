from agi_server.workflow.langgraph_runtime import (
    GrowthWorkflowState,
    LangGraphWorkflowRuntime,
    build_langgraph_workflow,
)


def test_build_langgraph_workflow_compiles():
    graph = build_langgraph_workflow()
    assert graph is not None


def test_langgraph_workflow_runtime_execution():
    runtime = LangGraphWorkflowRuntime()
    initial_state: GrowthWorkflowState = {
        "workflow_id": "test-diagnostic",
        "status": "pending",
        "context": {"company_id": "c-123"},
        "evidence_ids": ["ev_test_1"],
        "agent_results": {},
        "step_history": [],
    }

    result = runtime.execute(initial_state)

    assert result["status"] == "completed"
    assert "sync" in result["step_history"]
    assert "company_agent" in result["step_history"]
    assert "growth_agent" in result["step_history"]
    assert "review" in result["step_history"]
    assert "curator" in result["step_history"]
