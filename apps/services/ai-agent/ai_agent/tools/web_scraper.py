"""
Web scraping capability stub for the legacy ai-agent service.

This module is part of the unintegrated legacy microservice
(apps/services/ai-agent). All authorised web scraping in the production
baseline is gated behind the egress allowlist proxy (squid / ADR-0005) and
the ADR-0016 Phase 5 capability registry (web.scrape capability).

This file is intentionally a non-operational stub.  The original implementation
attempted direct external HTTP GET requests with no egress/policy control;
that path is pruned per the ADR-0016 Phase 5 "pruning" decision and LO-05
of the audit report (2026-07-27).

DO NOT restore unconditional outbound HTTP here. If web scraping is needed,
implement it as a gated capability handler in:
  apps/api/agi_server/agents/runtime.py
  apps/api/agi_server/agents/capabilities.py
following the scrape_web_page capability allowlist pattern and routing all
egress through the configured egress-gateway proxy.
"""

from __future__ import annotations


def scrape_web_page(url: str) -> str:
    """
    Stub: real web scraping is not available in the legacy ai-agent service.

    Raises NotImplementedError to prevent silent no-op behaviour.
    Implement web scraping as a gated capability in the primary agi_server
    agent runtime (ADR-0016 Phase 5).
    """
    raise NotImplementedError(
        f"Direct web scraping is disabled in the legacy ai-agent service. "
        f"URL '{url}' was not fetched. "
        "Use the authorised web.scrape capability in agi_server/agents/runtime.py "
        "which routes traffic through the egress-gateway allowlist proxy (ADR-0005)."
    )
