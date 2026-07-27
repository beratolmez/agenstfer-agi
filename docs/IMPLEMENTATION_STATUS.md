# Implementation Status

Last verified: 24 July 2026

This document is the authoritative statement of what the repository actually does versus the target architecture (ADR-0016).

## Implemented and Verified (Active Baseline)

### Platform and Trust Boundary

- [x] FastAPI monolithic backend service (`apps/api/agi_server`) exposing REST APIs, auth, model gateway, connectors, and diagnostics.
- [x] Primary React Web Console (`apps/web`) built with Vite, TypeScript, Vanilla CSS, and visual workflow inspector (`@xyflow/react`).
- [x] Database persistence using PostgreSQL / SQLite (via SQLAlchemy) for canonical entities, users, accounts, leads, evidence items, and audit records.

### Ingestion, Evidence, and Knowledge

- [x] Read-Only CRM (`ReadOnlyCRMConnector`) and ERP (`ReadOnlyERPConnector`) connector layer ingesting Accounts, Leads, Opportunities, Invoices, and Products.
- [x] Immutable content-addressed evidence locator generation (`ev_...`) ensuring resolution to persisted source records.
- [x] Filesystem & In-Memory OKF (Open Knowledge Format) bundle parsing (`FileSystemOKFBundle`) as immutable source of truth.
- [x] ChromaDB / QMD vector retrieval integration (`okf/search.py`, `rag_service/retrieve.py`) using active OKF bundle as source of truth, with automatic lexical fallback when vector service is unreachable, bounded 320-char snippets, and `ev_...` locator provenance (ADR-0016 Phase 6).
- [x] Approved Product-Owned MCP Client Gateway (`mcp.py`, `MCPProfile` DB model, Alembic migration `20260724_0008`) operating strictly on approved, read-only MCP profiles with code-defined tool allowlists, rejecting arbitrary user-provided URLs as execution authority (ADR-0016 Phase 7).
- [x] PostgreSQL `EventInbox` persistence and `EventDispatchQueue` worker (`events.py`, `triggers.py`, `scheduler.py`, Alembic migration `20260724_0009`) ingesting untrusted webhook payloads, enforcing idempotency deduplication, matching approved trigger rules, and executing strictly published workflow versions (ADR-0016 Phase 8).

### Model Gateway & Agent Runtime

- [x] Model Gateway abstraction (`agents/model_gateway.py`) supporting Google Gemini API and local/cloud GPU Ollama endpoints with dynamic API key model discovery (`/api/models/discover`).
- [x] Cloud opt-in deployment policy (`config.py`, `model_gateway.py`, `docker-compose.yml`, `docker-compose.cloud.yml`, `squid.conf`) running base local Compose without cloud provider/key requirements, enforcing explicit provider selection, mounted secret files in production, fail-closed data boundaries, and egress allowlists (ADR-0016 Phase 10).
- [x] Pydantic AI structured output probes (`agents/probe.py`) validating model connectivity and contract schemas (`CompanyAnalysis`, `OpportunityHypotheses`, `EvidenceReview`, `OKFChangeSet`).
- [x] Custom FastAPI Python agent execution runtime (`agents/runtime.py`) processing diagnostic steps with Pydantic AI helpers.
- [x] Typed LangGraph `StateGraph` foundation module (`workflow/langgraph_runtime.py`) and runtime seam supporting compiled StateGraph execution with Pydantic AI contracts (ADR-0016 Phase 2).
- [x] LangGraph `StateGraph` execution engine (`LangGraphWorkflowEngine`) powering the primary `builtin-growth-diagnostic` workflow with real pause/resume approval semantics on the same run ID, evidence gate validation, and Pydantic AI contracts (ADR-0016 Phase 3).
- [x] Control-plane prepared typed `ExecutionContext` (`context.py`) bounding run identity, actor, data classification, evidence locators, context budgets, and fail-closed privacy boundary validation across LangGraph short-term memory (ADR-0016 Phase 4).
- [x] Code-defined unified capability registry (`capabilities.py`) and runtime tool injection runtime (`ScopedCapabilityTools.for_spec`), ensuring published agent spec capabilities and workflow node scope allowlists operate on the exact same code-defined handlers, with workflow node scopes strictly narrowing (never expanding) published spec capabilities (ADR-0016 Phase 5).

### Product Journey & UI/UX

- [x] Onboarding Setup Wizard (`SetupWizard.tsx`) covering First Admin Bootstrap Gate, Company Profile, Model Gateway Discovery, CRM/ERP Connectors, OKF Ingestion, and System Ready state.
- [x] Visual Workflow Editor with `@xyflow/react` node graph and Inspector panel.
- [x] Aligned Growth Workflow Templates (`templates.py`, `registry_service.py`) referencing real published agent IDs, allowlisted model profiles, valid capability IDs, explicit executable vs catalog-only template metadata, and scope-bounded generic workflow publication rules (ADR-0016 Phase 9).
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
- **Phase 8 (Completed PostgreSQL Event Inbox & Durable Dispatch)**: Webhook events stored in PostgreSQL `EventInbox`, enforcing idempotency deduplication, trigger rule matching, and published workflow dispatch.
- **Phase 9 (Completed Template Alignment & Generic Workflow Publication)**: Aligned template catalogs with published agent specs, allowlisted model profiles, capability IDs, explicit executable/catalog-only metadata, and generic workflow publication rules while preserving read-only connectors.
- **Phase 10 (Completed Cloud Opt-In Policy & Secret File Boundary)**: Enforced base local Compose execution without cloud provider/key requirements, explicit cloud opt-in, production secret file boundary, and egress proxy allowlist consistency.
- **Phase 11 (Completed Content-Safe Telemetry, Production Kubernetes & Backup/Restore)**: Cleaned DBOS leftovers from backup/restore PowerShell routines, enforced content-safe telemetry boundary (excluding prompts, source bodies, evidence, secrets, and contact identifiers), and updated production Kubernetes manifests with agi-api control plane and agi-worker background worker topology without hardcoded secrets.
- **Phase 12 (Completed React Web Console Control Plane Integration)**: Integrated Setup Wizard onboarding progress with backend persisted state, aligned Workflow Editor inspector with published agent/capability allowlist APIs, and ensured UI state survives refresh without synthetic success text or mock execution.
- **Phase 13 (Completed Frontend Truthfulness Alignment)**: Removed synthetic mock scraping timers, fake percentage bars, and mock tasks from RAG visualizer and web scraping panel, querying real backend OKF validation state and presenting truthful bounded capability status across control plane surfaces.
- **Phase 14 (Completed Release Alignment & Legacy Documentation)**: Documented legacy microservice stubs (`apps/services/ai-agent`, `apps/services/rag`) as unintegrated legacy code, updated root README and repository maps, and aligned release checklist and evaluation plan with the active unified LangGraph/FastAPI/ChromaDB/MCP target architecture.
- **Phase 15 (Completed Model Gateway Auth & Setup Wizard Resolution - ADR-0017)**: Standardized Gemini Bearer token authentication for OpenAI-compatible endpoint, synchronized SetupProgress configuration schema allowed keys (`industry`, `provider`, `model`), enforced full-screen onboarding gate compliance, and improved probe error reporting.
- **Phase 16 (Completed Docker Network Egress & Setup Progress Completion - ADR-0018)**: Configured Docker Compose `app` service with egress proxy network routing (`HTTP_PROXY`/`HTTPS_PROXY` via `egress-gateway`), enabled non-blocking `completed_steps` resolution in `/api/setup/progress`, and eliminated onboarding infinite loop on Dashboard navigation.
- **Phase 17 (Completed Audit Report Runde 1 Critical Fixes - ADR-0019)**: Resolved `App.tsx` onboarding completion race condition, aligned 5-step onboarding progress schema in frontend and backend endpoints, enforced container network isolation by removing `app` from `egress` network to strictly force egress proxy routing via `egress-gateway`, and synchronized `docs/SYSTEM_ARCHITECTURE.md` with active runtime status.
- **Phase 18 (Completed Audit Report Runde 2 High Priority Fixes - ADR-0020)**: Aligned Vite proxy port target to 8080, cleaned non-prefixed `GEMINI_*` and deprecated `AGI_ENABLE_DBOS` variables from `.env.example` and `config.py`, persisted extended onboarding progress configuration (`model_profile`, `source_mode`, `locale`), updated `decideCandidate` response type in `api.ts`, fixed broken links in `README.md` and `OPERATIONS_RUNBOOK.md`, and marked `NEW_ARCHITECTURE_PLAN.md` with deprecation notice.
- **Phase 19 (Completed Audit Report Runde 3 Medium Priority Cleanup - ADR-0021)**: Implemented `GET /api/sources/{source_id}/preview` API endpoint, enriched `WorkflowRunDetail` TypeScript interfaces in `types.ts`, hardened `infra/proxy/nginx.conf` with WebSocket upgrade headers, gzip compression, and static asset caching, excluded `apps/frontend/` in `.dockerignore`, and updated `PROJECT_ARCHITECTURE.md` container deployment row.
- **Phase 20 (Completed Audit Report Runde 4 Low Priority Cleanup & Full Resolution - ADR-0022)**: Simplified observability runbook instructions in `OPERATIONS_RUNBOOK.md`, removed deprecated DBOS scripts (`cleanup_dbos.py`, `watch-workflow-restarts.sh`), archived orphan `NEW_ARCHITECTURE.yaml` to `docs/archive/`, linked `DOMAIN_CONTRACTS.md` and `PRODUCT_ROADMAP_TO_GOAL.md` in `README.md`, and finalized 100% resolution of all 32 technical audit report findings across Rounds 1-4.
- **Phase 21 (Completed First Diagnostic Workflow Registry Binding Fix - ADR-0023)**: Ensured platform agent registry auto-synchronization (`ensure_platform_registry`) during workflow binding validation, onboarding completion, and version publishing to guarantee built-in agent availability for initial diagnostic runs.
- **Phase 23 (Completed Agent Registry Binding Fallback Hardening - ADR-0023)**: Hardened `validate_workflow_bindings` with automatic fallback to latest published agent version when requested agent versions are not yet present in the database, and added `ensure_platform_registry` invocation to `save_workflow_draft` to prevent workflow draft validation failures.
- **Phase 22 (Completed Audit Report Runde 5 — Legacy Package Pruning - ADR-0025)**: Removed silent `TestModel()` fallback from `apps/services/ai-agent/ai_agent/models.py` (LO-04), replacing it with an explicit `RuntimeError` that surfaces Model Gateway failures instead of creating a second ungoverned inference path. Replaced synthetic web-scraper stub with a `NotImplementedError` guard documenting ADR-0016 Phase 5 pruning decision (LO-05). Removed the last DBOS-era docstring artefact from `apps/api/agi_server/workflow/runtime.py` (LO-06).


- **Phase 24 (Gemini Native Transport, Bounded Reasoning & Measured Output Budgets - ADR-0026)**: Moved the Gemini profile off the OpenAI-compatibility shim onto the native `google-genai` transport (`GoogleModel` + `GoogleProvider`), which round-trips the `thought_signature` Gemini 3.x requires on every follow-up tool turn — the OpenAI shim dropped it and every tool-using agent failed with HTTP 400. Removed the ineffective `parallel_tool_calls: False` mitigation (Gemini ignores it: asked for one tool call, returned three). Bounded reasoning per model family (`thinking_level: MINIMAL` for 3.x, `thinking_budget: 0` for 2.x) so hidden reasoning no longer consumes the typed-extraction budget. Disabled provider-side retries (`HttpRetryOptions(attempts=1)`) so one run cannot exhaust a free-tier daily quota. Raised `growth-opportunity-analyst` to v4 with `max_output_tokens: 2000` from a measured requirement of 1357 tokens; bumped `company-analyst` to v4 and `wiki-curator` to v3 for prompt-contract fixes and repinned `build_default_workflow` per ADR-0008. Stated the runtime-enforced `reports/*.md` rule in the `wiki-curator` prompt and made the rejection error name the offending paths. Resolved the `company-analyst` "at most one evidence ID per claim" contradiction against the evidence gate. Configured the control-plane logger at startup and stopped Alembic's `fileConfig` from disabling it, so failed runs now emit full tracebacks. Fixed three long-standing test failures: LangGraph checkpointer `thread_id`, probe nonce liveness check, and a fail-open evidence gate in `run_growth_diagnostic` (`_enforce_evidence_gate` was defined but never called there).

  **Status:** the built-in diagnostic now advances through 10 of 11 nodes against a live Gemini model. The remaining stop is the evidence gate itself — see `docs/AUDIT_FINDINGS.md` Tur 3 for the open product decision on all-or-nothing gating versus excluding unsupported claims as data gaps.
