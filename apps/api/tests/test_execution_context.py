import pytest
from agi_server.context import ContextBudget, ExecutionContext
from pydantic import ValidationError


def test_execution_context_creation_and_defaults():
    ctx = ExecutionContext(
        run_id="run-123",
        workflow_id="builtin-growth-diagnostic",
        workflow_version=1,
    )
    assert ctx.run_id == "run-123"
    assert ctx.workflow_id == "builtin-growth-diagnostic"
    assert ctx.workflow_version == 1
    assert ctx.data_classification == "internal"
    assert ctx.bounded_evidence_ids == []
    assert ctx.context_budget.max_input_tokens == 4000
    assert ctx.context_budget.max_output_tokens == 1000


def test_execution_context_privacy_boundary_cloud_confidential_restricted_fails_closed():
    local_ctx = ExecutionContext(
        run_id="run-restricted-local",
        workflow_id="builtin-growth-diagnostic",
        data_classification="restricted",
    )
    # Local GPU calls allowed even for restricted data
    local_ctx.validate_privacy_boundary(cloud=False)

    cloud_ctx = ExecutionContext(
        run_id="run-confidential-cloud",
        workflow_id="builtin-growth-diagnostic",
        data_classification="confidential",
    )
    with pytest.raises(PermissionError, match="Cloud model profile cannot process"):
        cloud_ctx.validate_privacy_boundary(cloud=True)

    cloud_restricted_ctx = ExecutionContext(
        run_id="run-restricted-cloud",
        workflow_id="builtin-growth-diagnostic",
        data_classification="restricted",
    )
    with pytest.raises(PermissionError, match="Cloud model profile cannot process"):
        cloud_restricted_ctx.validate_privacy_boundary(cloud=True)

    # Cloud call allowed for internal / public data
    cloud_internal_ctx = ExecutionContext(
        run_id="run-internal-cloud",
        workflow_id="builtin-growth-diagnostic",
        data_classification="internal",
    )
    cloud_internal_ctx.validate_privacy_boundary(cloud=True)


def test_execution_context_sanitize_for_prompt_excludes_raw_bodies_and_secrets():
    ctx = ExecutionContext(
        run_id="run-456",
        workflow_id="builtin-growth-diagnostic",
        actor_id="admin-user-1",
        data_classification="internal",
        bounded_evidence_ids=["ev_anka_001", "ev_anka_002"],
        retrieval_references=[
            {
                "id": "ev_anka_001",
                "type": "invoice",
                "title": "Invoice Excerpt",
                "snippet": "Sanitized invoice summary",
                "raw_secret": "API_SECRET_KEY_DO_NOT_EXPOSE",
            }
        ],
    )
    sanitized = ctx.sanitize_for_prompt()
    assert sanitized["run_id"] == "run-456"
    assert sanitized["data_classification"] == "internal"
    assert sanitized["bounded_evidence_ids"] == ["ev_anka_001", "ev_anka_002"]
    assert len(sanitized["retrieval_references"]) == 1
    assert "raw_secret" not in sanitized["retrieval_references"][0]


def test_context_budget_bounds_enforced():
    budget = ContextBudget(max_input_tokens=8000, max_output_tokens=2000)
    assert budget.max_input_tokens == 8000
    assert budget.max_output_tokens == 2000

    with pytest.raises(ValidationError):
        ContextBudget(max_input_tokens=10)  # ge=100
