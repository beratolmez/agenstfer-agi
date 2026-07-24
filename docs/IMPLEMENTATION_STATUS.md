# Implementation Status

Last verified: 24 July 2026

This document is the authoritative statement of what the repository actually does versus the target architecture (ADR-0016).

## Implemented and Verified (Active Baseline)

### Platform and Trust Boundary

- [x] FastAPI monolithic backend service (`apps/api/agi_server`) exposing REST APIs, auth, model gateway, connectors, and diagnostics.
- [x] Primary React Web Console (`apps/web`) built with Vite, TypeScript, Tailwind CSS, and visual workflow inspector (`@xyflow/react`).
- [x] Database persistence using PostgreSQL / SQLite (via SQLAlchemy) for canonical entities, users, accounts, leads, evidence items, and audit records.

### Ingestion, Evidence, and Knowledge

- [x] Read-Only CRM (`ReadOnlyCRMConnector`) and ERP (`ReadOnlyERPConnector`) connector layer ingesting Accounts, Leads, Opportunities, Invoices, and Products.
- [x] Immutable content-addressed evidence locator generation (`ev_...`) ensuring resolution to persisted source records.
- [x] Filesystem & In-Memory OKF (Open Knowledge Format) bundle parsing (`FileSystemOKFBundle`) as immutable source of truth.
- [x] ChromaDB / QMD vector retrieval integration (`okf/search.py`, `rag_service/retrieve.py`) using active OKF bundle as source of truth, with automatic lexical fallback when vector service is unreachable, bounded 320-char snippets, and `ev_...` locator provenance (ADR-0016 Phase 6).
- [x] Approved Product-Owned MCP Client Gateway (`mcp.py`, `MCPProfile` DB model, Alembic migration `20260724_0008`) operating strictly on approved, read-only MCP profiles with code-defined tool allowlists, rejecting arbitrary user-provided URLs as execution authority (ADR-0016 Phase 7).

### Model Gateway & Agent Runtime

- [x] Model Gateway abstraction (`agents/model_gateway.py`) supporting Google Gemini API and local/cloud GPU Ollama endpoints with dynamic API key model discovery (`/api/models/discover`).
- [x] Pydantic AI structured output probes (`agents/probe.py`) validating model connectivity and contract schemas (`CompanyAnalysis`, `OpportunityHypotheses`, `EvidenceReview`, `OKFChangeSet`).
- [x] Custom FastAPI Python agent execution runtime (`agents/runtime.py`) processing diagnostic steps with Pydantic AI helpers.
- [x] Typed LangGraph `StateGraph` foundation module (`workflow/langgraph_runtime.py`) and runtime seam supporting compiled StateGraph execution with Pydantic AI contracts (ADR-0016 Phase 2).
- [x] LangGraph `StateGraph` execution engine (`LangGraphWorkflowEngine`) powering the primary `builtin-growth-diagnostic` workflow with real pause/resume approval semantics on the same run ID, evidence gate validation, and Pydantic AI contracts (ADR-0016 Phase 3).
- [x] Control-plane prepared typed `ExecutionContext` (`context.py`) bounding run identity, actor, data classification, evidence locators, context budgets, and fail-closed privacy boundary validation across LangGraph short-term memory (ADR-0016 Phase 4).
- [x] Code-defined unified capability registry (`capabilities.py`) and runtime tool injection runtime (`ScopedCapabilityTools.for_spec`), ensuring published agent spec capabilities and workflow node scope allowlists operate on the exact same code-defined handlers, with workflow node scopes strictly narrowing (never expanding) published spec capabilities (ADR-0016 Phase 5).

### Product Journey & UI/UX

- [x] Onboarding Setup Wizard (`SetupWizard.tsx`) covering First Admin Bootstrap Gate, Company Profile, Model Gateway Discovery, CRM/ERP Connectors, OKF Ingestion, and System Ready state.
- [x] Visual Workflow Editor with `@xyflow/react` node graph and Inspector panel.
- [x] Single authoritative architecture documentation (`docs/SYSTEM_ARCHITECTURE.md`) updated with ADR-0016 migration roadmap.

---

## Current Architecture Gaps & Non-Production Components

The following components exist as target specifications, test stubs, or legacy artifacts, and are **NOT** active production capabilities in the current runtime:

1. **LangGraph Orchestrator**: LangGraph `StateGraph` execution engine (`LangGraphWorkflowEngine`) is active for the primary `builtin-growth-diagnostic` workflow with control-plane prepared `ExecutionContext` memory and unified capability allowlist tool injection. Custom fallback runtime remains for non-built-in workflows, and native Postgres checkpointers will be enabled in subsequent phases.
2. **ChromaDB Integration**: ChromaDB / QMD vector search is active in `okf/search.py` with automatic lexical fallback when unreachable; active OKF bundle remains sole source of truth and candidate bundles are never indexed.
3. **MCP Protocol**: Product-owned approved MCP Client Gateway (`mcp.py`) is active for read-only tools on code-defined allowlists; arbitrary user-provided URL execution is strictly disabled.
4. **Event Log & Tracing**: Basic audit logging is persisted to PostgreSQL, but full self-hosted Langfuse telemetry pipeline integration is target specification.
5. **Legacy Microservices & Mock UIs**: `apps/services/ai-agent` and `apps/services/rag` are unintegrated legacy microservices; `apps/frontend/dashboard-ui` and `apps/frontend/web-ui` are non-production mock surfaces. `apps/api/agi_server` and `apps/web` are the only active production baseline.

---

## Unified Target Architecture Migration Roadmap (ADR-0016)

- **Phase 1 (Completed)**: Architectural audit, documentation alignment, and ADR-0016 creation.
- **Phase 2 (Completed Foundation Seam)**: Typed LangGraph `StateGraph` foundation module (`langgraph_runtime.py`) and unit tests implemented.
- **Phase 3 (Completed Built-in Diagnostic)**: LangGraph `StateGraph` execution engine implemented and active for `builtin-growth-diagnostic` with pause/resume approval semantics, evidence gate, and Pydantic AI contracts.
- **Phase 4 (Completed ExecutionContext & Memory)**: Control-plane prepared typed `ExecutionContext` implemented, enforcing data classification boundary and prompt sanitization.
- **Phase 5 (Completed Capability Allowlist Alignment)**: Published agent capability specs and runtime tool injection aligned to a single code-defined allowlist registry (`capabilities.py`), enforcing capability narrowing rules.
- **Phase 6 (Completed Active OKF & Chroma Retrieval)**: Knowledge retrieval integrated with ChromaDB disposable derived index using active OKF bundle as source of truth and seamless lexical fallback.
- **Phase 7 (Completed Approved Product-Owned MCP Gateway)**: Implemented product-owned read-only `MCPGateway` and `MCPProfile` persistence, rejecting arbitrary user-provided execution URLs.


