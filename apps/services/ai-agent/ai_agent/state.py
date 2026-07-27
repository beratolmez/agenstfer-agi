import operator
from collections.abc import Sequence
from typing import Annotated, TypedDict


class AgentState(TypedDict, total=False):
    messages: Annotated[Sequence[str], operator.add]
    context: str
    current_agent: str

    # Intermediate agent research/review data
    research_data: str
    analysis_data: str
    final_review: str

    # 7 Specialized KDS AI ABS Agent Node Outputs
    company_profiling_data: str
    lead_opportunity_data: str
    competitor_intelligence_data: str
    security_audit_data: str
    financial_diagnostics_data: str
    seo_brand_intelligence_data: str
    customer_satisfaction_data: str
