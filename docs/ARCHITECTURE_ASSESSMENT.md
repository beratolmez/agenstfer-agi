# Architecture Assessment

**Assessed:** 28 July 2026 · **Baseline:** `f5ba673` · **Method:** full read of the PRD,
`SYSTEM_ARCHITECTURE.md`, `IMPLEMENTATION_STATUS.md`, the MCP layer, the capability engine,
agent specs, the workflow layer and the repository tree, plus a live end-to-end run of the
built-in diagnostic against a real Gemini model.

Every claim below carries a `file:line` reference. Items fixed after the assessment are
marked in **[Since this assessment](#since-this-assessment)**; the body describes the state
as found, so the record stays honest.

---

## Current Architecture

A single-process FastAPI monolith with a React SPA. The only Python package that ships is
`agi_server` (`pyproject.toml:39-41`); the image runs `uvicorn agi_server.main:app`
(`Dockerfile:24`).

| Layer | Actual state | Location |
|---|---|---|
| HTTP API | one 2470-line module, ~70 endpoints, no router split | `agi_server/main.py` |
| Orchestration | LangGraph `StateGraph`, compiled as a straight chain | `workflow/langgraph_runtime.py` |
| Agent runtime | Pydantic AI, `PromptedOutput`, 4 published specs | `agents/runtime.py`, `agents/specs/*.yaml` |
| Model Gateway | 2 local (Ollama) + 4 cloud providers; Gemini on the **native** `google-genai` transport | `agents/model_gateway.py:17-33` |
| Data | PostgreSQL / SQLite, 9 Alembic migrations | `db.py`, `alembic/versions/` |
| Knowledge | OKF 0.1 Markdown, Git-backed bundle + content-addressed raw vault | `okf/`, `ingestion/` |
| Retrieval | `qmd` HTTP service + lexical fallback (**no `chromadb` dependency**) | `okf/search.py:7` |
| Frontend | React 19 + Vite, hash-based manual routing, 10 features | `apps/web/src` |
| Deployment | Docker Compose; `core` network `internal: true` + Squid egress allowlist | `docker-compose.yml`, `infra/egress/squid.conf` |

**The working path:** `POST /api/diagnostics/run` → `start_persisted_workflow` → LangGraph
engine → 12 nodes → `awaiting_approval` → `POST /api/approvals/{id}/decision` → OKF
candidate merge → `completed`.

**Scale:** 47 backend source files · 13 `NodeKind` values · 4 agent specs · 11 capabilities ·
28 ADRs · 32 backend test files + 8 frontend + 3 Playwright e2e.

---

## Strengths

**1. The evidence and provenance chain is the strongest part of the system.**
- Immutable, content-addressed raw vault with a manifest (`ingestion/service.py:171-197`)
- Excerpt hashes are re-verified against the immutable snapshot on every read; a mismatch
  raises rather than degrading (`ingestion/service.py:328-329`)
- Deterministic metric receipts are stored as their own `EvidenceItem` with a verified
  source digest (`domain/metrics.py:85-125`)
- Tiered evidence gate: a rejected numeric claim is fatal, a rejected narrative claim is
  withheld and reported as an attributed data gap (`diagnostics/service.py:405-456`, ADR-0027)

**2. Versioning and immutability are enforced in code, not just documented.** Published
versions cannot be edited and new versions only come from a clone
(`registry_service.py:117-129`); agent versions are pinned into the definition at publish
(`:249-251`) and frozen again at run start (`persistent_runtime.py:296-300`).

**3. Security boundaries are fail-closed and tested.** Cloud opt-in is validated at import
time (`config.py:60-63`); `confidential`/`restricted` content cannot reach a cloud model
(`agents/runtime.py:78-85`); the Squid allowlist is covered by a test
(`test_model_gateway.py:195`); the control-plane policy cannot be overridden by an agent
prompt (`model_gateway.py:35-49`); the container runs non-root on digest-pinned images.

**4. Human-in-the-loop is real.** Pause and resume happen on the same run ID
(`persistent_runtime.py:709-794`), guarded by `SELECT … FOR UPDATE` and a decision
idempotency constraint (`db.py:280-281`).

**5. The graph validator is substantial** — 14 rules covering single trigger, exactly one
approval, approval ordering after all report outputs, acyclicity, reachability, edge type
compatibility, condition branch completeness and a field-injection guard
(`workflow/validator.py:17-173`).

**6. Test discipline is genuine** — a real-model end-to-end journey, a post-restore state
test, and dedicated security control tests.

---

## Weaknesses

**1. LangGraph is present in name, not in semantics.** `add_conditional_edges` is never
used; the graph is the straight chain of the topological order
(`langgraph_runtime.py:79-83`). `interrupt_before`/`interrupt_after` are absent (`:86`)
even though `DOMAIN_CONTRACTS.md:41` and ADR-0016 claim otherwise. The checkpointer is a
`MemorySaver` rebuilt on every run (`:70,85`), so resume comes from the database and the
checkpointer is decorative. Conditional branching is hand-emulated through
`state_data["_active_edges"]` plus `status="skipped"`.

**2. Only 4 of 13 node kinds do real work.** No-ops: the three trigger kinds,
`normalize_context` (`:279-280`), `okf_compile` (`:281-282`), `knowledge_search`
(`:283-284` — it copies config into state and performs no search) and `policy_check`
(`:291-294` — unconditionally writes `"passed"`). Real: `deterministic_score`, `condition`,
`agent_run`, `report_output`. **Retrieval is not part of the workflow graph at all.**

**3. Three parallel execution paths plus two stubs.** The LangGraph engine; a fallback loop
whose control flow, approval handling and skip logic are copy-pasted
(`persistent_runtime.py:479-606`); the dead `run_growth_diagnostic`
(`diagnostics/service.py:518-720`); a `build_langgraph_workflow` stub; and the `runtime.py`
dry-run path. Engine selection is a hardcoded ID set (`persistent_runtime.py:468-477`), and
because `builtin-` is a reserved prefix (`main.py:2153-2159`) a user-authored workflow can
never reach the LangGraph engine.

**4. MCP does not exist in practice.** The policy layer is real (`mcp.py:33-70`) but the
transport returns a fixed dictionary (`:76-80`), `transport_type` is never read,
`MCPGateway` is never constructed by production code, and no `MCPProfile` row is ever
seeded — the table is always empty.

**5. Most capabilities are not wired.** Four do real work, one is proposal-only by design,
four are `planned` stubs, and two (`mcp.query`, `mcp.read_resource`) are mapped to the
wrong handler and bound to nothing (`capabilities.py:95,103`). Node-level narrowing exists
(`persistent_runtime.py:347-350`) but no node in the shipped workflow sets `capabilities`.

**6. Templates are a showcase.** The four "executable" templates pass the validator but
cannot run: their connector IDs are not registered, none contains `deterministic_score`, and
`report_output` requires all four agent results (`persistent_runtime.py:399-405`). No route
calls `get_executable_templates()`.

**7. 80% of trigger rules are dead** — four of five point at workflow IDs that are never
seeded and cannot be created through the API (`triggers.py:27-64`).

**8. Tight coupling to demo data.** `data_source_sync` ignores `connector_id` and always
syncs the demo company; `SignalId` is a five-value `Literal`; and the PRD's five
business-domain contracts exist only as schemas that `output_type` will not admit.

---

## Risks

| # | Risk | Level | Evidence |
|---|---|---|---|
| R1 | `scheduler_loop` had no `try/except`; one error killed all scheduling for the process lifetime, silently | HIGH | `scheduler.py:177-183` |
| R2 | `active_step.node_id` does not exist (`step_id`), so the error handler raised inside itself and runs stayed `running` forever | HIGH (confirmed) | `persistent_runtime.py:578` vs `db.py:248` |
| R3 | `MCPProfile.server_url` does not exist (`server_identity`); `/api/sources/test-mcp` always returned 500 | MEDIUM (confirmed) | `main.py:1554` vs `db.py:331` |
| R4 | `asyncio.create_task` result is not retained — a background run can be garbage-collected mid-flight | MEDIUM | `persistent_runtime.py:690` |
| R5 | Synchronous DB and model calls run on the event loop; no `run_in_executor` | MEDIUM | — |
| R6 | Postgres 5432 and Ollama 11434 are published to the host even though `core` is `internal` | MEDIUM | `docker-compose.yml:53-54,98-99` |
| R7 | Free-tier quota is 20 requests/day/model; one diagnostic costs 4+ calls | MEDIUM (operational) | measured |
| R8 | Published `definition` is rewritten at publish with no content hash or signature | LOW | `registry_service.py:279` |

---

## Technical Debt

**Dead code:** the `apps/api/main.py` shim (87 lines, kept alive only by
`test_api_main.py`) · `apps/services/ai-agent` + `rag` (21 files, zero production imports) ·
`run_growth_diagnostic` (~200 lines) · `build_langgraph_workflow` +
`LangGraphWorkflowRuntime` · `StructuredOutputProbe` · `list_capabilities()` ·
`EventTriggerEngine._event_log` (so `/api/triggers/events` is always empty) · 14 empty
`.gitkeep` directories.

**Broken scripts:** `qualify-model.*` invoked a file absent from the image, breaking the
`release-rehearsal.sh:181` chain · `backup.sh`/`restore.sh` depended on the removed DBOS
database, and `backup.ps1` had already diverged · `backup-customer-state.*` archived the
wrong source · `release-rehearsal.sh:154` passed a compose profile that does not exist.

**Doc/code contradictions:** `IMPLEMENTATION_STATUS.md:3` date stale, `:20-21` claimed
ChromaDB and MCP were active · `DOMAIN_CONTRACTS.md:30,41` claimed a PostgreSQL checkpointer
and `interrupt_*` · "ChromaDB" appeared in four places with no such dependency · ADR-0002 and
ADR-0011 are gutted "DELETED" stubs with no superseding pointer · ADR number 4 is used twice.

**Other:** `main.py` 2470 lines · `SetupWizard.tsx` 985 lines · `WorkflowEditor.tsx:187`
hardcodes a capability fallback list containing six non-working entries while omitting two
working ones · `test_workflow_templates.py:69` reads the wrong shape and asserts nothing ·
`templates.py:212,230` returns and mutates a module-level dict without copying · two parallel
deployment definitions · no dedicated tests for `scheduler.py`, `registry_service.py`,
`probe.py`, `okf/git_repo.py`, `okf/compiler.py`, `http_security.py`.

---

## Scaling Blockers

Decisions that work today but will not survive a second customer or the first real load.

| # | Decision | Why it blocks scaling |
|---|---|---|
| SB-1 | `SignalId` is a five-value `Literal` (`agents/contracts.py:7-13`) and `metrics.py:191-210` matches Turkish product names as strings | The opportunity taxonomy is baked into one demo company. For a second customer the diagnostic either emits demo data or raises `ValueError`. **The hardest blocker to productisation.** |
| SB-2 | `data_source_sync` ignores `connector_id` and always syncs the demo company (`persistent_runtime.py:272-278`) | Real CRM/ERP data can never enter the workflow |
| SB-3 | Synchronous DB and model calls on one event loop, no `run_in_executor`, background task reference not retained (`persistent_runtime.py:690`) | No concurrent runs; a long agent call blocks the whole API; tasks can be collected mid-run |
| SB-4 | Engine choice is a hardcoded ID set (`persistent_runtime.py:468-477`) plus the reserved `builtin-` prefix (`main.py:2153-2159`) | User workflows can never use the LangGraph engine; the second runtime is copy-paste maintenance |
| SB-5 | LangGraph as a straight chain: no conditional edges, no interrupts, `MemorySaver` per run (`langgraph_runtime.py:70,79-86`) | Parallel branches, durable resume and long-lived human approval cannot scale — and the docs claim otherwise |
| SB-6 | `PROFILES` is two fixed local entries plus one synthetic cloud profile (`model_gateway.py:17-33`) | The intended per-customer / per-agent low-mid-high tiering with limits and billing does not fit |
| SB-7 | `main.py` is 2470 lines with ~70 endpoints | Merge contention and poor test isolation as the team grows |
| SB-8 | Published `definition` is rewritten at publish with no content hash (`registry_service.py:279`) | Version integrity cannot be audited; compliance claims cannot be proven |
| SB-9 | Single-company install (AGENTS.md) versus PRD §9 multi-tenant isolation — **the contradiction is recorded in no ADR** | The data-boundary architecture cannot be chosen until the commercial model is settled |
| SB-10 | Retrieval sits outside the workflow graph; `knowledge_search` is a no-op (`persistent_runtime.py:283-284`) | RAG quality cannot be measured or improved as the knowledge base grows |

---

## Missing Documents

1. **Policy Engine and Consent Ledger design** — PRD §6.3/§6.4 call these core; there is no
   code and no ADR or design document either.
2. **Growth Context Graph data model / ERD** — PRD §6.1 lists 25 entities; the generic
   infrastructure exists but the target mapping is undocumented.
3. **API reference** — ~70 endpoints, no exported OpenAPI or endpoint catalogue.
4. **Model tiering / quota / cost policy** — nothing exists for the stated roadmap goal.
5. **Real-customer onboarding runbook** — only the demo path is documented.
6. **Prompt versioning policy** — required by PRD §6.7.
7. **Security control → test mapping** — `THREAT_MODEL.md` exists but nothing maps controls
   to the tests that prove them.
8. **SLO / capacity plan** — ADR-0012's "capacity policy" clause was never filled in.

---

## Missing Decisions

**Settled on 29 July 2026** — the five that blocked the most work:

1. ✅ Multi-tenancy → single-tenant, isolation by deployment separation (ADR-0032)
2. ✅ LangGraph depth → PostgreSQL checkpointer and `interrupt_*`, chain topology retained (ADR-0029)
3. ✅ Engine consolidation → one engine, selected by a definition property (ADR-0029)
4. ✅ MCP → target specification; tools ship as native capabilities (ADR-0030)
5. ✅ Retrieval → OKF Wiki and vector are **one layer with two paths**, not a choice (ADR-0031)

Still open:

6. Local model set — the diagram says GLM 5.2 / QWEN 3.7 Max, the code says `qwen3.5:9b/27b`
7. Deployment target — Compose or Kubernetes/Terraform
8. Demo-data decoupling — when does `SignalId` stop being a `Literal`
9. The fate of `planned` capabilities beyond `web.scrape`
10. Mature form of the evidence gate — should narrative claims be repaired rather than withheld

---

## Since this assessment

Work completed against these findings, tracked in `docs/REMEDIATION_ROADMAP.md`:

- **R1, R2, R3 fixed** with regression tests that fail against the old code (ADR-0028)
- **Dead code removed**: the `apps/api/main.py` shim, `apps/services/*`, 14 empty scaffold
  directories, `run_growth_diagnostic`, the `build_langgraph_workflow` stub,
  `StructuredOutputProbe`, `list_capabilities()`, and five unreferenced scripts
- **Broken scripts repaired**: DBOS references removed from backup/restore, the nonexistent
  `--profile cloud` dropped; the missing model-qualification harness now fails loudly
  instead of cryptically
- **Doc contradictions corrected** in `IMPLEMENTATION_STATUS.md`, `SYSTEM_ARCHITECTURE.md`
  and `DOMAIN_CONTRACTS.md`

Everything else remains open and is prioritised in the roadmap.

---

## Confidence: 88%

**High (95%+):** backend architecture, workflow semantics, agent and capability structure,
MCP status, repository inventory, dead-code findings. The code was read directly, the system
was run end-to-end against a live model, and R2/R3 were confirmed line-by-line against the
`db.py` column lists.

**Medium (70-80%):** frontend behaviour (the UI was not exercised in a browser) ·
correctness of the `infra/kubernetes` and `terraform` manifests (only their
unreferencedness was verified) · broken scripts identified by static tracing rather than
execution.

**Out of scope:** performance and load measurement, penetration testing, dependency CVE
scanning.
