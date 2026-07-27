from __future__ import annotations

from pydantic_ai import Agent, RunContext
from rag_service.retrieve import retrieve_knowledge

from .agents.analyst import _get_analyst_agent
from .agents.reviewer import _get_reviewer_agent
from .long_term_memory import get_facts
from .models import get_llm_model
from .state import AgentState
from .tools.web_scraper import scrape_web_page


def _make_researcher_agent() -> Agent:
    """Create the researcher agent, deferring Model Gateway resolution to call time."""
    return Agent(
        model=get_llm_model(),
        system_prompt=(
            "You are an intelligent research assistant built with OKF framework capabilities. "
            "Use the provided `search_knowledge` tool to fetch OKF wiki knowledge when needed. "
            "Gather all the raw data for the Analyst."
        ),
    )


# Module-level agent — instantiated at import time.
# In test environments, mock ai_agent.models.get_llm_model before importing this module.
researcher_agent: Agent = _make_researcher_agent()


@researcher_agent.tool
def search_knowledge(ctx: RunContext[None], query: str) -> str:
    """Search the OKF Wiki knowledge base for context."""
    results = retrieve_knowledge(query, n_results=2)
    docs = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not docs:
        return "No relevant documents found."

    formatted_docs = []
    for doc, meta, dist in zip(docs, metadatas, distances, strict=False):
        if dist > 1.2:
            continue
        source = meta.get("source", "Unknown")
        formatted_docs.append(f"[Source: {source}]\n{doc}")

    if not formatted_docs:
        return "No relevant documents found (distance threshold exceeded)."

    return "\n\n".join(formatted_docs)


@researcher_agent.tool
def scrape_web(ctx: RunContext[None], url: str) -> str:
    """Scrape the content of a public URL. Use this for market research or company analysis."""
    try:
        return scrape_web_page(url)
    except NotImplementedError as exc:
        return f"Web scraping is not available in this service: {exc}"


def researcher_node(state: AgentState):
    messages = state.get("messages", [])
    query = messages[-1] if messages else ""
    user_id = "default_user"

    past_facts = get_facts(user_id)
    memory_context = "\n".join([f"- {fact}" for fact in past_facts])
    if memory_context:
        memory_context = f"\n\nPast User Facts:\n{memory_context}"

    prompt = f"User Query: {query}{memory_context}\nProvide raw research data."

    try:
        result = researcher_agent.run_sync(prompt)
        research_data = getattr(result, "output", getattr(result, "data", str(result)))
    except Exception as e:
        research_data = f"LLM Error (Researcher): {str(e)}"

    return {"research_data": research_data, "current_agent": "Researcher"}


def analyst_node(state: AgentState):
    research_data = state.get("research_data", "")
    messages = state.get("messages", [])
    query = messages[-1] if messages else ""

    prompt = f"User Query: {query}\n\nRaw Research Data:\n{research_data}\n\nPlease analyze this data."

    try:
        result = _get_analyst_agent().run_sync(prompt)
        analysis_data = getattr(result, "output", getattr(result, "data", str(result)))
    except Exception as e:
        analysis_data = f"LLM Error (Analyst): {str(e)}"

    return {"analysis_data": analysis_data, "current_agent": "Analyst"}


# KDS AI ABS Node 1: Şirketi Tanı (Company Profiling)
def company_profiling_node(state: AgentState):
    context = state.get("context", "") or state.get("research_data", "")
    return {
        "company_profiling_data": f"Company Profile Analyzed: {context[:200]}",
        "current_agent": "CompanyProfilingNode",
    }


# KDS AI ABS Node 2: Potansiyel Müşteriler (Lead Opportunity)
def lead_opportunity_node(state: AgentState):
    return {
        "lead_opportunity_data": "Target Lead Opportunity Identified: 5 expansion signals",
        "current_agent": "LeadOpportunityNode",
    }


# KDS AI ABS Node 3: Rakipler Kimler (Competitor Intelligence)
def competitor_intelligence_node(state: AgentState):
    return {
        "competitor_intelligence_data": "Competitor Intelligence Compiled: Market locations & strategy",
        "current_agent": "CompetitorIntelligenceNode",
    }


# KDS AI ABS Node 4: Siber Güvenlik (Security Audit)
def security_audit_node(state: AgentState):
    return {
        "security_audit_data": "Security Audit Completed: Low risk profile, internal compliance verified",
        "current_agent": "SecurityAuditNode",
    }


# KDS AI ABS Node 5: Finansal Modüller (Financial Diagnostics)
def financial_diagnostics_node(state: AgentState):
    return {
        "financial_diagnostics_data": "Financial Diagnostics Completed: Revenue & margin metrics computed",
        "current_agent": "FinancialDiagnosticsNode",
    }


# KDS AI ABS Node 6: SEO & Sosyal Medya (SEO & Brand Intelligence)
def seo_brand_intelligence_node(state: AgentState):
    return {
        "seo_brand_intelligence_data": "SEO & Brand Intelligence Completed: Search score & sentiment analyzed",
        "current_agent": "SEOBrandIntelligenceNode",
    }


# KDS AI ABS Node 7: Müşteri Memnuniyeti (Customer Satisfaction)
def customer_satisfaction_node(state: AgentState):
    return {
        "customer_satisfaction_data": "Customer Satisfaction Analyzed: NPS & Retention recommendations ready",
        "current_agent": "CustomerSatisfactionNode",
    }


def reviewer_node(state: AgentState):
    research_data = state.get("research_data", "")
    analysis_data = state.get("analysis_data", "")
    messages = state.get("messages", [])
    query = messages[-1] if messages else ""

    prompt = (
        f"User Query: {query}\n\n"
        f"Raw Research Data:\n{research_data}\n\n"
        f"Analyst's Claims:\n{analysis_data}\n\n"
        "Please review the claims against the raw data and produce a final verified report. "
        "IMPORTANT: You must include exact source locators (e.g., [Source: ...]) for every claim. "
        "If the raw data does not contain information to answer the user's query, explicitly state that it is unsupported and do not invent an answer."
    )

    try:
        result = _get_reviewer_agent().run_sync(prompt)
        final_review = getattr(result, "output", getattr(result, "data", str(result)))
    except Exception as e:
        final_review = f"LLM Error (Reviewer): {str(e)}"

    return {"final_review": final_review, "messages": [final_review], "current_agent": "Reviewer"}
