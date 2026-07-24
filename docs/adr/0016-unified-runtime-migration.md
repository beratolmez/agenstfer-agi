# ADR-0016: Unified Target Architecture and Custom Runtime Migration

* Status: Accepted
* Date: 2026-07-24
* Deciders: Antigravity AI Team & Architecture Committee

## Context and Problem Statement

The repository currently exhibits a transitional state between the target production specification and the initial custom implementation:

1. **Backend & Orchestration**: The active backend (`apps/api/agi_server`) runs a custom Python orchestration loop (`agents/runtime.py`). The architectural specification targets LangGraph `StateGraph` state machines with PostgreSQL checkpointers.
2. **Vector Storage & RAG**: Active OKF search in `agi_server` uses in-memory / filesystem content parsing. ChromaDB exists in a separate, unintegrated service (`apps/services/rag`).
3. **MCP Integration**: Connector management includes a mock/test endpoint (`/api/sources/test-mcp`), but full Model Context Protocol (MCP) server/client protocol integration is not yet active.
4. **Legacy & Mock Surfaces**: Legacy microservices (`apps/services/ai-agent`, `apps/services/rag`) and mock UI directories (`apps/frontend/dashboard-ui`, `apps/frontend/web-ui`) coexist alongside the primary runtime (`apps/api/agi_server` and `apps/web`).

To eliminate ambiguity and prevent claiming non-verified components as production-ready capabilities, a unified architecture decision and migration plan must be formally recorded.

## Decision Drivers

- **Honesty in Capability Reporting**: Clearly distinguish between active, repository-verified capabilities in `agi_server` and target or mock architectural components.
- **Single Operational Baseline**: Establish `apps/api/agi_server` (FastAPI) + `apps/web` (React UI) as the sole active runtime baseline.
- **Architectural Alignment**: Maintain LangGraph, Pydantic AI, ChromaDB, and standardized MCP as the target architecture while structuring a phased migration path.
- **Clean Separation**: Mark legacy microservices (`apps/services/*`) and mock UI surfaces (`apps/frontend/*`) as deprecated/test artifacts.

## Decision Outcome

Adopt **Unified Target Architecture** as the single destination architecture for Agentic Growth Intelligence (AGI) and execute Phase 1 (Documentation and Alignment):

### 1. Architectural Blueprint (Target State)
- **Control Plane**: FastAPI (`apps/api/agi_server`) exposing unified REST endpoints and Model Gateway.
- **Workflow State Machine**: LangGraph `StateGraph` managing node transitions, PostgreSQL state checkpointers, and human-in-the-loop (`interrupt_before`/`interrupt_after`) approvals.
- **Agent Node Execution**: Pydantic AI contracts and agents providing typed outputs and structured inference.
- **Vector Retrieval**: Native ChromaDB integration embedded into `agi_server` RAG service.
- **Connector Interface**: Standardized MCP (Model Context Protocol) integration replacing ad-hoc test endpoints.
- **Frontend Console**: React UI (`apps/web`) as the single B2B web console.

### 2. Migration Phases
- **Phase 1 (Completed)**: Documentation and gap analysis. Reclassify active vs. target capabilities across `IMPLEMENTATION_STATUS.md`, `SYSTEM_ARCHITECTURE.md`, and ADR-0016.
- **Phase 2 (Completed Foundation Seam)**: Implemented typed LangGraph `StateGraph` foundation module (`langgraph_runtime.py`) and verified unit tests without disrupting existing custom persistent runtime API endpoints.
- **Phase 3 (Completed Built-in Diagnostic)**: Migrated `builtin-growth-diagnostic` workflow execution to LangGraph `StateGraph` engine (`LangGraphWorkflowEngine`), preserving Pydantic AI contracts, version pins, idempotency, evidence gate, and pause/resume approval semantics on the same run ID.
- **Phase 4 (Completed ExecutionContext & Memory)**: Implemented typed `ExecutionContext` (`context.py`), ensuring control plane prepares bounded context, context budgets, and fail-closed privacy boundaries across LangGraph short-term memory.
- **Phase 5 (Completed Capability Allowlist Alignment)**: Published agent capability specs and runtime tool injection aligned to a single code-defined allowlist registry (`capabilities.py`), enforcing capability narrowing rules.
- **Phase 6 (Completed Active OKF & Chroma Retrieval)**: Integrated knowledge retrieval with ChromaDB disposable derived index using active OKF bundle as immutable source of truth and seamless lexical fallback.
- **Phase 7 (Completed Approved Product-Owned MCP Gateway)**: Implemented product-owned read-only `MCPGateway` and `MCPProfile` persistence, rejecting arbitrary user-provided execution URLs.
- **Phase 8 (Completed PostgreSQL Event Inbox & Durable Dispatch)**: Webhook events stored in PostgreSQL `EventInbox`, enforcing idempotency deduplication, trigger rule matching, and published workflow dispatch.
- **Phase 9 (Completed Template Alignment & Generic Workflow Publication)**: Aligned template catalogs with published agent specs, allowlisted model profiles, capability IDs, explicit executable/catalog-only metadata, and generic workflow publication rules while preserving read-only connectors.

## Consequences

- **Positive**:
  - Accurately aligns status documentation with repository reality.
  - Eliminates false claims regarding LangGraph, ChromaDB, and MCP in current production execution.
  - Provides a clear, non-breaking roadmap for phase-by-phase architectural consolidation.
- **Negative / Trade-offs**:
  - Temporary coexistence of custom runtime while Phase 2-4 migrations are executed.
