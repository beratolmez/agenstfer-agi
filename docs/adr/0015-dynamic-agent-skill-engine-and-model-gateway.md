# ADR-0015: Dynamic Agent Skill Engine and Multi-Provider Model Gateway

* Status: Accepted
* Date: 2026-07-21
* Deciders: Antigravity AI Team & Product Management

## Context and Problem Statement

Different B2B growth workflows require different specialized capabilities (e.g. web scraping, CRM reading, ERP financial analysis, battlecard generation). Furthermore, development and testing environments may not possess dedicated local GPU hardware, necessitating flexible Model Gateway support for free/cloud API providers alongside customer-dedicated local GPU endpoints.

## Decision Drivers

- **Modularity & Skill Binding**: Enable administrators to dynamically assign built-in capabilities (`search_knowledge`, `scrape_web`, `read_crm`, `read_erp`, `generate_battlecard`) to specific AI agent nodes via the React UI Inspector.
- **Provider Flexibility**: Seamless support for Google Gemini API, Groq Cloud, Mistral AI, OpenRouter, and Ollama/vLLM local/cloud GPU endpoints.
- **Data Privacy & Governance**: Cloud model calls strictly filter confidential/restricted payloads according to settings and approval boundaries.

## Decision Outcome

Chosen Option: Built-in Capability Registry (`capabilities.py`), Pydantic AI dynamic tool injection runtime, and multi-provider Model Gateway.

### Consequences

- **Positive**:
  - Developers and administrators can configure agent skills visually in the React UI.
  - Zero hard dependency on local GPU hardware during development/testing phase.
  - Structured output probe validation ensures API key validity before workflow execution.
