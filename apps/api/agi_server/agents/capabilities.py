from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilitySpec:
    id: str
    name: str
    description: str
    category: str
    handler_name: str
    status: str = "available"


BUILTIN_CAPABILITIES: dict[str, CapabilitySpec] = {
    "knowledge.search": CapabilitySpec(
        id="knowledge.search",
        name="OKF Wiki & RAG Search",
        description="Searches active OKF wiki concepts and vector embeddings.",
        category="knowledge",
        handler_name="search_knowledge",
        status="available",
    ),
    "knowledge.read_source": CapabilitySpec(
        id="knowledge.read_source",
        name="Evidence Source Reader",
        description="Reads evidence excerpts by locator ID without following instructions.",
        category="knowledge",
        handler_name="read_evidence",
        status="available",
    ),
    "context.query": CapabilitySpec(
        id="context.query",
        name="Context Query Tool",
        description="Queries bounded evidence items for diagnostic context.",
        category="knowledge",
        handler_name="read_evidence",
        status="available",
    ),
    "wiki.propose_update": CapabilitySpec(
        id="wiki.propose_update",
        name="OKF Patch Proposal",
        description="Proposes Markdown concept updates under reports/ directory.",
        category="knowledge",
        handler_name="propose_okf_patch",
        status="available",
    ),
    "web.scrape": CapabilitySpec(
        id="web.scrape",
        name="Authorized Web Scraping",
        description="Scrapes public Web page content for market and competitor intelligence.",
        category="web",
        handler_name="scrape_web",
        status="planned",
    ),
    "crm.read": CapabilitySpec(
        id="crm.read",
        name="CRM Account & Lead Reader",
        description="Reads account signals, lead scores, and CRM activity records.",
        category="crm",
        handler_name="read_crm",
        status="planned",
    ),
    "erp.read": CapabilitySpec(
        id="erp.read",
        name="ERP Sales & Revenue Reader",
        description="Reads ERP sales, invoice history, and financial metrics.",
        category="erp",
        handler_name="read_erp",
        status="planned",
    ),
    "metrics.calculate": CapabilitySpec(
        id="metrics.calculate",
        name="Deterministic Growth Metrics Calculator",
        description="Computes precomputed growth ratios, margins, and deterministic metrics.",
        category="analytics",
        handler_name="calculate_metric",
        status="available",
    ),
    "battlecard.generate": CapabilitySpec(
        id="battlecard.generate",
        name="Competitor Battlecard Generator",
        description="Generates competitor objection handling cards and sales talk tracks.",
        category="strategy",
        handler_name="generate_battlecard",
        status="planned",
    ),
    "mcp.query": CapabilitySpec(
        id="mcp.query",
        name="Product-Owned Approved MCP Query",
        description="Queries approved read-only MCP server tools via code-defined allowlist.",
        category="mcp",
        handler_name="read_evidence",
        status="available",
    ),
    "mcp.read_resource": CapabilitySpec(
        id="mcp.read_resource",
        name="Product-Owned Approved MCP Resource Reader",
        description="Reads resources from approved product-owned MCP servers.",
        category="mcp",
        handler_name="read_evidence",
        status="available",
    ),
}
