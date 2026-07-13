from agi_server.workflow import build_default_workflow, validate_workflow
from agi_server.workflow.models import WorkflowEdge


def test_default_workflow_is_valid_and_topologically_sorted():
    workflow = build_default_workflow()
    result = validate_workflow(workflow)
    assert result.valid, result.issues
    assert result.topological_order[0] == "trigger"
    assert result.topological_order[-1] == "report"


def test_cycle_is_rejected():
    workflow = build_default_workflow()
    workflow.edges.append(
        WorkflowEdge(
            id="cycle",
            source="report",
            target="trigger",
            data_type="artifact",
        )
    )
    result = validate_workflow(workflow)
    assert not result.valid
    assert any(issue.code == "graph.cycle" for issue in result.issues)


def test_type_mismatch_is_rejected():
    workflow = build_default_workflow()
    workflow.edges[0].data_type = "knowledge"
    result = validate_workflow(workflow)
    assert not result.valid
    assert any(issue.code.startswith("edge.") for issue in result.issues)
