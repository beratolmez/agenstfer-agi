from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CapabilitySpec:
    id: str
    name: str
    description: str
    category: str
    handler_name: str


BUILTIN_CAPABILITIES: dict[str, CapabilitySpec] = {
    "knowledge.search": CapabilitySpec(
        id="knowledge.search",
        name="OKF Wiki & RAG Search",
        description="Searches active OKF wiki concepts and ChromaDB vector embeddings.",
        category="knowledge",
        handler_name="search_knowledge",
    ),
    "web.scrape": CapabilitySpec(
        id="web.scrape",
        name="Authorized Web Scraping",
        description="Scrapes public Web page content for market and competitor intelligence.",
        category="web",
        handler_name="scrape_web",
    ),
    "crm.read": CapabilitySpec(
        id="crm.read",
        name="CRM Account & Lead Reader",
        description="Reads account signals, lead scores, and CRM activity records.",
        category="crm",
        handler_name="read_crm",
    ),
    "erp.read": CapabilitySpec(
        id="erp.read",
        name="ERP Sales & Revenue Reader",
        description="Reads ERP sales, invoice history, and financial metrics.",
        category="erp",
        handler_name="read_erp",
    ),
    "metrics.calculate": CapabilitySpec(
        id="metrics.calculate",
        name="Deterministic Growth Metrics Calculator",
        description="Computes precomputed growth ratios, margins, and deterministic metrics.",
        category="analytics",
        handler_name="calculate_metric",
    ),
    "battlecard.generate": CapabilitySpec(
        id="battlecard.generate",
        name="Competitor Battlecard Generator",
        description="Generates competitor objection handling cards and sales talk tracks.",
        category="strategy",
        handler_name="generate_battlecard",
    ),
}


def list_capabilities() -> list[dict[str, Any]]:
    """Return serializable capability registry items for API / UI consumption."""
    return [
        {
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "category": item.category,
        }
        for item in BUILTIN_CAPABILITIES.values()
    ]
