from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

DataClassification = Literal["public", "internal", "confidential", "restricted"]


class ContextBudget(BaseModel):
    max_input_tokens: int = Field(default=4000, ge=100, le=128000)
    max_output_tokens: int = Field(default=1000, ge=50, le=32000)
    max_evidence_items: int = Field(default=20, ge=1, le=500)


class ExecutionContext(BaseModel):
    """Control-plane prepared execution context for agent nodes and memory."""

    run_id: str
    workflow_id: str
    workflow_version: int = 1
    actor_id: str | None = None
    data_classification: DataClassification = "internal"
    bounded_evidence_ids: list[str] = Field(default_factory=list)
    retrieval_references: list[dict[str, Any]] = Field(default_factory=list)
    model_policy_revision: str = "v1"
    context_budget: ContextBudget = Field(default_factory=ContextBudget)

    def validate_privacy_boundary(self, *, cloud: bool) -> None:
        """Enforces fail-closed privacy boundary before sending context to LLMs."""
        if cloud and self.data_classification in {"confidential", "restricted"}:
            msg = f"Cloud model profile cannot process {self.data_classification} data"
            raise PermissionError(msg)

    def sanitize_for_prompt(self) -> dict[str, Any]:
        """Returns a sanitized dict view for prompt context without secrets or raw bodies."""
        return {
            "run_id": self.run_id,
            "workflow_id": self.workflow_id,
            "workflow_version": self.workflow_version,
            "data_classification": self.data_classification,
            "bounded_evidence_ids": self.bounded_evidence_ids,
            "retrieval_references": [
                {
                    "id": ref.get("id"),
                    "type": ref.get("type"),
                    "title": ref.get("title"),
                    "snippet": ref.get("snippet"),
                }
                for ref in self.retrieval_references
            ],
            "model_policy_revision": self.model_policy_revision,
        }
