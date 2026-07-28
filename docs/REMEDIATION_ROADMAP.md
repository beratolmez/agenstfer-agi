# Remediation Roadmap

Derived from [ARCHITECTURE_ASSESSMENT.md](./ARCHITECTURE_ASSESSMENT.md). Ordered by
impact × cost × risk, not by severity alone: a cheap fix that stops silent data loss outranks
an expensive refactor with the same severity label.

**Size:** S ≈ under a day · M ≈ a few days · L ≈ a week or more.
**Status:** ✅ done · 🔜 next · ⬜ open · 🔒 blocked on a decision.

---

## P0 — Silent failures

| ID | Item | Size | Status |
|---|---|---|---|
| R1 | `scheduler_loop` had no `try/except`; one bad tick killed all scheduling and event dispatch for the process lifetime, with nothing logged | S | ✅ ADR-0028 |
| R2 | `active_step.node_id` (column is `step_id`) made the fallback runtime's error handler raise inside itself: the real error was lost, `error_json` never written, the run stayed `running` forever | S | ✅ ADR-0028 |
| R3 | `MCPProfile.server_url` (column is `server_identity`) made `/api/sources/test-mcp` return 500 on every real request; the only test passed `db=None` and never reached the bug | S | ✅ ADR-0028 |

All three now have regression tests that fail against the old code.

---

## P1 — Truthfulness

The system claimed capabilities it does not have. That is the most damaging class of defect
in an evidence-based product, because it is invisible until someone depends on it.

| ID | Item | Size | Status |
|---|---|---|---|
| T1 | `IMPLEMENTATION_STATUS.md` claimed ChromaDB and MCP were active; `DOMAIN_CONTRACTS.md` claimed a PostgreSQL checkpointer and `interrupt_*` | S | ✅ ADR-0028 |
| T2 | Dead code removed: `apps/api/main.py` shim, `apps/services/*`, 14 empty scaffold dirs, `run_growth_diagnostic`, `build_langgraph_workflow` stub, `StructuredOutputProbe`, `list_capabilities()`, 5 unreferenced scripts | M | ✅ ADR-0028 |
| T3 | Broken scripts: DBOS references in backup/restore, nonexistent `--profile cloud`, missing qualification harness now fails loudly | S | ✅ ADR-0028 |
| T4 | **Model qualification harness** — the golden-eval runner was built on the removed legacy stack and never shipped inside the image, so this release gate has not run for some time. Rebuild it on `agi_server.evaluation` so it is packaged with the application | M | 🔜 |
| T5 | `planned` capabilities are indistinguishable from working ones in the API and UI: the seeded `definition` omits `status`, and `WorkflowEditor.tsx:187` hardcodes a fallback list of six non-working capabilities while omitting two working ones | S | ⬜ |
| T6 | `mcp.query` / `mcp.read_resource` are mapped to the `read_evidence` handler and bound to nothing. Either wire them or remove them from the registry | S | 🔒 depends on D4 |
| T7 | Four of five trigger rules target workflow IDs that are never seeded and cannot be created via the API. `EventInbox` also reports `no_match` when a rule *did* match but the target was unpublished | S | ⬜ |
| T8 | `test_workflow_templates.py:69` reads the wrong node shape, so that test asserts nothing | S | ⬜ |

---

## P2 — Productisation prerequisites

Nothing below P2 matters commercially until these are done: a second customer is not
possible without them.

| ID | Item | Size | Status |
|---|---|---|---|
| SB-1 | `SignalId` is a five-value `Literal` and metric derivation matches Turkish product names as strings. The opportunity taxonomy must come from configuration or the OKF bundle instead of being compiled in | L | 🔒 depends on D8 |
| SB-2 | `data_source_sync` ignores `connector_id` and always syncs the demo company, so real CRM/ERP data cannot enter a workflow. Drive it from registered `DataSource` rows | M | ⬜ |
| SB-2b | The four workflow templates pass the validator but cannot execute: unregistered connector IDs, no `deterministic_score` node, and `report_output` requires all four agent results. Either make them runnable or mark them catalog-only | M | ⬜ |

---

## P3 — Durability

| ID | Item | Size | Status |
|---|---|---|---|
| SB-3a | Background runs use `asyncio.create_task` without retaining the reference; CPython may collect the task mid-run | S | ⬜ |
| SB-3b | Synchronous SQLAlchemy and model calls execute on the API event loop. Move workflow execution to the worker topology that already exists in the Kubernetes manifests, or at minimum off the loop | L | ⬜ |
| SB-4 | Engine selection is a hardcoded ID set, and the reserved `builtin-` prefix means user workflows can never reach the LangGraph engine. Consolidate onto one engine, or select by a definition attribute rather than by ID | M | 🔒 depends on D3 |
| R6 | Postgres 5432 and Ollama 11434 are published to the host despite `core` being an internal network. Convenient in development, an unnecessary surface in a customer install — split by compose overlay | S | ⬜ |

---

## P4 — Maturity

| ID | Item | Size | Status |
|---|---|---|---|
| SB-5 | Adopt real LangGraph semantics: `add_conditional_edges`, `interrupt_before`/`interrupt_after`, and a PostgreSQL checkpointer that survives restart. Today the graph is a straight chain and the checkpointer is rebuilt per run | L | 🔒 depends on D2 |
| SB-10 | `knowledge_search` is a no-op, so retrieval sits outside the graph and its quality cannot be measured. Wire the node to `KnowledgeSearch` | M | 🔒 depends on D5 |
| SB-6 | Model tiering: per-customer and per-agent low/mid/high profiles, Langfuse tracing, usage limits and billing hooks. `PROFILES` is currently two fixed local entries plus one synthetic cloud profile | L | 🔒 depends on D10 |
| N1 | Six of 13 node kinds write a constant string and complete: three triggers, `normalize_context`, `okf_compile`, `knowledge_search`. `policy_check` unconditionally writes `"passed"`. Implement or remove from the catalogue so the editor stops offering inert nodes | M | ⬜ |
| N2 | Missing dedicated tests: `scheduler.py`, `registry_service.py`, `probe.py`, `okf/git_repo.py`, `okf/compiler.py`, `http_security.py` | M | ⬜ |

---

## P5 — Structural

| ID | Item | Size | Status |
|---|---|---|---|
| SB-7 | Split `main.py` (2470 lines, ~70 endpoints) into routers. Real regression risk — must be its own change, with no other work in the same commit | L | ⬜ |
| SB-8 | Published `definition` is rewritten at publish with no content hash or signature, so version integrity cannot be audited | M | ⬜ |
| F1 | `SetupWizard.tsx` is 985 lines; the frontend has no router (hash-based dispatch in `App.tsx`) | M | ⬜ |
| F2 | No frontend tests for `EventPanel`, `Knowledge`, `Opportunities`, `WebScrapingPanel`, `RagVisualizer`, `Sidebar`, `Topbar` | M | ⬜ |

---

## Open decisions

These block the items marked 🔒. Each needs an ADR before the work can start.

| ID | Decision | Blocks |
|---|---|---|
| D1 | **Multi-tenancy.** PRD §9 requires tenant isolation; AGENTS.md mandates a single-company install. The contradiction is recorded nowhere | data-boundary architecture |
| D2 | **LangGraph depth.** Stay with the straight chain, or adopt conditional edges + interrupts + a PostgreSQL checkpointer | SB-5 |
| D3 | **Engine consolidation.** Two runtimes or one | SB-4 |
| D4 | **MCP.** Finish the transport or reclassify as target specification | T6 |
| D5 | **Retrieval identity.** ChromaDB or qmd, and does retrieval belong in the graph | SB-10 |
| D6 | **Local model set.** The manager's diagram says GLM 5.2 / QWEN 3.7 Max; the code says `qwen3.5:9b/27b` | — |
| D7 | **Deployment target.** Compose, or the unreferenced Kubernetes/Terraform definition | — |
| D8 | **Demo-data decoupling.** Where does the signal taxonomy come from once it is no longer a `Literal` | SB-1 |
| D9 | **`planned` capabilities.** Implement or remove | T5, T6 |
| D10 | **Model tiering and billing.** Profile model, quota enforcement point, Langfuse boundary | SB-6 |

---

## Suggested sequence

1. **T4, T5, T7, T8** — finish P1. Cheap, and it stops the system overstating itself.
2. **D1, D2, D3, D5** — record the four decisions that block the most work. Documents, not code.
3. **SB-2, SB-2b** — make real connector data reachable; this is the first step that changes
   what the product can actually do for a customer.
4. **SB-3a, R6** — cheap durability and surface-area wins.
5. **D8 → SB-1** — decouple the signal taxonomy. The single largest unlock for a second customer.
6. **SB-3b, SB-4, SB-5** — the durability and orchestration rebuild, once the decisions exist.
7. **SB-7** — split `main.py` on its own, when nothing else is in flight.
