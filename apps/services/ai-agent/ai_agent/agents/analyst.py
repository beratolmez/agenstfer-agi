from __future__ import annotations

from pydantic_ai import Agent

from ..models import get_llm_model

# Agent is instantiated lazily (at first use) to avoid a module-level
# get_llm_model() call that raises RuntimeError when the Model Gateway /
# Ollama endpoint is not available in test or CI environments.
_analyst_agent: Agent | None = None


def _get_analyst_agent() -> Agent:
    global _analyst_agent
    if _analyst_agent is None:
        _analyst_agent = Agent(
            model=get_llm_model(),
            system_prompt=(
                "You are the Company Analyst. Your job is to process raw research data "
                "and extract concrete growth opportunities, potential risks, and actionable insights. "
                "You only rely on the provided research data. Do not invent new facts."
            ),
        )
    return _analyst_agent


# Legacy compatibility: expose analyst_agent as a property-like accessor.
# Code that does `analyst_agent.run_sync(...)` must call `_get_analyst_agent()` instead.
# The module-level name is kept for import compatibility but is None until first use.
analyst_agent = None  # type: ignore[assignment]  # use _get_analyst_agent() in nodes.py
