from langgraph.graph import END, START, StateGraph

from .nodes import (
    analyst_node,
    company_profiling_node,
    competitor_intelligence_node,
    customer_satisfaction_node,
    financial_diagnostics_node,
    lead_opportunity_node,
    researcher_node,
    reviewer_node,
    security_audit_node,
    seo_brand_intelligence_node,
)
from .state import AgentState


def create_graph(checkpointer=None):
    workflow = StateGraph(AgentState)

    # Core nodes
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("analyst", analyst_node)

    # KDS AI ABS 7 Specialized Nodes
    workflow.add_node("company_profiling", company_profiling_node)
    workflow.add_node("lead_opportunity", lead_opportunity_node)
    workflow.add_node("competitor_intelligence", competitor_intelligence_node)
    workflow.add_node("security_audit", security_audit_node)
    workflow.add_node("financial_diagnostics", financial_diagnostics_node)
    workflow.add_node("seo_brand_intelligence", seo_brand_intelligence_node)
    workflow.add_node("customer_satisfaction", customer_satisfaction_node)

    # Final review node
    workflow.add_node("reviewer", reviewer_node)

    # Define edges (Sequential Pipeline connecting research -> diagnostic nodes -> reviewer)
    workflow.add_edge(START, "researcher")
    workflow.add_edge("researcher", "analyst")
    workflow.add_edge("analyst", "company_profiling")
    workflow.add_edge("company_profiling", "lead_opportunity")
    workflow.add_edge("lead_opportunity", "competitor_intelligence")
    workflow.add_edge("competitor_intelligence", "security_audit")
    workflow.add_edge("security_audit", "financial_diagnostics")
    workflow.add_edge("financial_diagnostics", "seo_brand_intelligence")
    workflow.add_edge("seo_brand_intelligence", "customer_satisfaction")
    workflow.add_edge("customer_satisfaction", "reviewer")
    workflow.add_edge("reviewer", END)

    app = workflow.compile(checkpointer=checkpointer)
    return app
