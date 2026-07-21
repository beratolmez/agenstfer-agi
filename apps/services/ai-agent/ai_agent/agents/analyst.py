from pydantic_ai import Agent
from ..models import get_llm_model

analyst_agent = Agent(
    model=get_llm_model(),
    system_prompt=(
        "You are the Company Analyst. Your job is to process raw research data "
        "and extract concrete growth opportunities, potential risks, and actionable insights. "
        "You only rely on the provided research data. Do not invent new facts."
    ),
)
