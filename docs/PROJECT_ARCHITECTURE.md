# Agentic Growth Intelligence — Product Architecture & Business Mapping

**Status:** Commercial Product Target; MVP qualification active  
**Deployment Model:** Customer-private, single-installation per company  
**Technical Architecture Specification:** Refer to [docs/SYSTEM_ARCHITECTURE.md](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/docs/SYSTEM_ARCHITECTURE.md)

---

## 1. Product Purpose & Value Proposition

The Agentic Growth Intelligence (AGI) platform unifies company documents, web snapshots, and ERP/CRM read-only connectors into an evidence-backed knowledge graph and growth diagnostic system.

Upon onboarding, the system generates:
- Evidence-linked company profile and analysis.
- Top growth expansion opportunities.
- A 30-day actionable execution plan with citation links.

---

## 2. Manager Architectural Mapping

| Vision Concept | System Architecture Mapping | Technology Stack | Notes |
|---|---|---|---|
| **KDS AI ABS** | Growth Intelligence Control Plane | FastAPI, LangGraph, Pydantic AI | Core orchestration state machine |
| **Local / Cloud GPU** | Model Gateway | Gemini API, Ollama, vLLM, LM Studio | Flexible LLM provider abstraction |
| **Şirket Dokümanları & Web** | Ingestion & Vector RAG | RAG Service, ChromaDB | OKF 0.1 Markdown sources |
| **Container Stack** | Isolated Customer Deployment | Docker Compose (Reference Deployment) | FastAPI Monolithic Control Plane & Worker |
| **Ajan Düğümleri** | Specialized Agent Nodes | Pydantic AI + LangGraph | Company Analysis, Competitor Intel, Security, Financial, SEO, Satisfaction |
| **İnsan Onayı** | Approval Center | LangGraph interrupt_before/after | Human-in-the-loop approval workflow |
| **Management & Modules** | Read-Only Adapters | React UI, FastAPI, PostgreSQL | Dashboard, ERP, CRM, Documents, Reports, Social Media, Web |
| **Observability** | Telemetry Sink | Langfuse | Self-hosted tracing across LLMs & Tools |

---

## 3. Core Product Boundaries (MVP)

1. **Read-Only Systems Access**: MVP connects to external CRM/ERP/Document stores strictly via read-only adapters. External write operations or messaging actions require explicit human approval via the Approval Center.
2. **Data Residency & Security**: Data sent to external LLM providers follows strict confidentiality filtering. Customer deployments remain isolated in their respective AWS VPC or private infrastructure.
3. **Single Source of Truth**: For detailed technical diagrams and sequence flows, refer to [SYSTEM_ARCHITECTURE.md](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/docs/SYSTEM_ARCHITECTURE.md).
