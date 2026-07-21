from pydantic_ai import Agent
from ..models import get_llm_model

reviewer_agent = Agent(
    model=get_llm_model(),
    system_prompt=(
        "You are the Evidence Reviewer. Your job is to double-check the Company Analyst's claims "
        "against the raw research data to ensure there is no hallucination. "
        "Output the final polished report for the user, verifying that all insights are grounded in evidence."
    ),
)
