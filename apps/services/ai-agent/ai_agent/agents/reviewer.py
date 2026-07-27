from __future__ import annotations

from pydantic_ai import Agent

from ..models import get_llm_model

# Lazy instantiation — see analyst.py for rationale.
_reviewer_agent: Agent | None = None


def _get_reviewer_agent() -> Agent:
    global _reviewer_agent
    if _reviewer_agent is None:
        _reviewer_agent = Agent(
            model=get_llm_model(),
            system_prompt=(
                "You are the Evidence Reviewer. Your job is to double-check the Company Analyst's claims "
                "against the raw research data to ensure there is no hallucination. "
                "Output the final polished report for the user, verifying that all insights are grounded in evidence."
            ),
        )
    return _reviewer_agent


reviewer_agent = None  # type: ignore[assignment]  # use _get_reviewer_agent() in nodes.py
