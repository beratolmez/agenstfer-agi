# Remediation Roadmap

Derived from [ARCHITECTURE_ASSESSMENT.md](./ARCHITECTURE_ASSESSMENT.md) and **re-sequenced on
29 July 2026** against the five decisions now accepted (ADR-0029 … ADR-0033).

Ordered by impact × cost × risk, not by severity alone: a cheap fix that stops silent data
loss outranks an expensive refactor carrying the same label.

**Size:** S ≈ under a day · M ≈ a few days · L ≈ a week or more.
**Status:** ✅ done · 🔜 next · ⬜ open.

**Picking up work from here:** turn a row into a task packet before starting — goal, files,
change, out of scope, verification command, done-when. The structure and the reasoning are in
[`AI_DEVELOPMENT_GUIDE.md`](./AI_DEVELOPMENT_GUIDE.md) §8. One row is usually one packet; a
whole priority band never is.

---

## What the decisions changed

| Decision | Outcome | Effect on this roadmap |
|---|---|---|
| ADR-0029 | LangGraph Option C + engine consolidation | SB-5 narrows to checkpointer + interrupts; SB-4 merges into it as one change |
| ADR-0030 | MCP → target specification | MCP transport leaves the roadmap; tools ship as native capabilities. T6 shrinks to a cleanup |
| ADR-0031 | **OKF Wiki + vector as one retrieval layer** | SB-10 grows and splits: a cheap correctness fix moves up to P1, the hybrid build lands in P4 |
| ADR-0032 | Single-tenant confirmed | Unblocks boundary scoping; adds a PRD §9 amendment task |
| ADR-0033 | Model tiering, staged in three | SB-6 becomes three sequenced items, persistence first |

The largest re-ordering is retrieval. ADR-0031 made wiki and vector one layer rather than a
choice, which turns "pick a vector store" into two distinct pieces of work: a citation
**integrity** defect that is cheap and belongs early, and a hybrid retrieval **capability**
that only pays off once there is real customer knowledge to retrieve.

---

## P0 — Silent failures ✅

| ID | Item | Status |
|---|---|---|
| R1 | `scheduler_loop` had no `try/except`; one bad tick killed all scheduling for the process lifetime | ✅ ADR-0028 |
| R2 | `active_step.node_id` made the fallback runtime's error handler raise inside itself; runs stayed `running` forever | ✅ ADR-0028 |
| R3 | `MCPProfile.server_url` made `/api/sources/test-mcp` return 500 on every real request | ✅ ADR-0028 |
| R4 | Wizard's dropdown default overrode the deployment model; that model's per-minute free-tier cap is below what one diagnostic issues | ✅ ADR-0028 follow-up |
| R5 | Cloud redaction corrupted hex evidence ids in prompts, so the gate rejected supported claims | ✅ ADR-0028 follow-up |

---

## P1 — Integrity and truthfulness

The system claimed capabilities it lacked and emitted citations that could not be
dereferenced. In an evidence product this is the most damaging class of defect, because it is
invisible until someone relies on it.

| ID | Item | Size | Status |
|---|---|---|---|
| T1 | Docs claimed ChromaDB, MCP, a Postgres checkpointer and `interrupt_*` that did not exist | S | ✅ ADR-0028 |
| T2 | Dead code removed: legacy shim, `apps/services/*`, dead orchestrator, stubs, 14 empty dirs | M | ✅ ADR-0028 |
| T3 | Broken scripts: DBOS references, nonexistent compose profile, missing qualification harness now fails loudly | S | ✅ ADR-0028 |
| T9 | Editor no longer invents capabilities from a hardcoded list; `planned` ones are unselectable | S | ✅ ADR-0028 follow-up |
| **T10** | **Retrieval emits `ev_concept_…` locators with no `EvidenceItem` behind them.** Per ADR-0031 §4 a result carries a resolved locator or none — never a synthesised one | **S** | **🔜** |
| **T11** | **`knowledge_search` records what it retrieved** (query, mode, concept paths, resolved locators) into run state. Minimal version of ADR-0031 §6; makes retrieval auditable before the hybrid build | **S** | **🔜** |
| T6 | Remove the two dead `mcp.*` capabilities and reclassify MCP as target specification across the docs (ADR-0030) | S | 🔜 |
| T12 | Amend PRD §9 to deployment-level tenant isolation (ADR-0032) | S | ✅ |
| T4 | Rebuild the model qualification harness on `agi_server.evaluation` so it ships inside the image; the gate has not run for some time | M | ⬜ |
| T7 | Four of five trigger rules target workflow ids that are never seeded; `EventInbox` reports `no_match` when a rule matched but the target was unpublished | S | ⬜ |
| T8 | `test_workflow_templates.py:69` reads the wrong node shape and asserts nothing | S | ⬜ |

---

## P2 — Productisation prerequisites

Nothing below matters commercially until these land: a second customer is not possible
without them, and they are what make retrieval quality worth improving.

| ID | Item | Size | Status |
|---|---|---|---|
| SB-2 | `data_source_sync` ignores `connector_id` and always syncs the demo company, so real CRM/ERP data cannot enter a workflow. Drive it from registered `DataSource` rows | M | ⬜ |
| SB-1 | `SignalId` is a five-value `Literal` and metric derivation matches Turkish product names as strings. The opportunity taxonomy must come from configuration or the OKF bundle | L | ⬜ |
| SB-2b | The four "executable" templates pass the validator but cannot run: unregistered connector ids, no `deterministic_score`, `report_output` requires all four agent results | M | ⬜ |

---

## P3 — Durability

| ID | Item | Size | Status |
|---|---|---|---|
| SB-3a | Background runs use `asyncio.create_task` without retaining the reference; the task can be collected mid-run | S | ⬜ |
| SB-5+SB-4 | **One change per ADR-0029:** add the PostgreSQL checkpointer and `interrupt_before` on approval, and drive engine selection from a definition property instead of a hardcoded id set, converging the two runtimes | L | ⬜ |
| SB-3b | Move workflow execution off the API event loop onto the worker topology the Kubernetes manifests already describe | L | ⬜ |
| R6 | Postgres 5432 and Ollama 11434 are published to the host despite `core` being internal — split by compose overlay | S | ⬜ |

---

## P4 — Retrieval as designed (ADR-0031)

Deliberately after P2: hybrid retrieval over a synthetic demo dataset demonstrates little.
Once real customer knowledge is flowing, this is what makes it usable.

| ID | Item | Size | Status |
|---|---|---|---|
| SB-10a | Move the vector service out of `profiles: [search]` into the default topology, so a shipped install actually has the hybrid layer | S | ⬜ |
| SB-10b | Hybrid retrieval: run structural and vector paths, merge by concept path, dedupe and rank; record which mode served each result | M | ⬜ |
| SB-10c | Bind reindex to candidate approval — the only moment the source of truth changes | S | ⬜ |
| SB-10d | Rename the four "ChromaDB" references to describe the capability, not a product; keep `qmd` named only where the concrete adapter is discussed | S | ⬜ |

---

## P5 — Model tiering (ADR-0033, staged)

| ID | Item | Size | Status |
|---|---|---|---|
| SB-6a | **Persistence first.** Provider, model and encrypted key move out of the in-memory `Settings` singleton into the database. Independently fixes configuration being lost on restart while `setup_completed` stays true | M | ⬜ |
| SB-6b | Tier indirection: specs declare `low` / `standard` / `high`; the tier resolves from installation-scoped configuration with an optional per-agent override | M | ⬜ |
| SB-6c | Governance: budgets, pre-flight rejection before a request is spent, content-safe Langfuse attribution within the ADR-0010 boundary | L | ⬜ |
| D6 | Reconcile the local model set — the diagram names GLM 5.2 / QWEN 3.7 Max, the code pins `qwen3.5:9b/27b` | S | ⬜ |

---

## P6 — Maturity and structure

| ID | Item | Size | Status |
|---|---|---|---|
| N1 | Six of 13 node kinds write a constant string and complete; `policy_check` unconditionally writes `"passed"`. Implement or remove from the catalogue | M | ⬜ |
| N2 | Missing dedicated tests: `scheduler.py`, `registry_service.py`, `probe.py`, `okf/git_repo.py`, `okf/compiler.py`, `http_security.py` | M | ⬜ |
| SB-8 | Published `definition` is rewritten at publish with no content hash, so version integrity cannot be audited | M | ⬜ |
| SB-7 | Split `main.py` (2470 lines, ~70 endpoints) into routers. Real regression risk — its own change, nothing else in the commit | L | ⬜ |
| F1 | `SetupWizard.tsx` is 985 lines; the frontend has no router (hash dispatch in `App.tsx`); `i18n/index.ts` is imported nowhere and all strings are inline Turkish | M | ⬜ |
| F2 | No frontend tests for `EventPanel`, `Knowledge`, `Opportunities`, `WebScrapingPanel`, `RagVisualizer`, `Sidebar`, `Topbar` | M | ⬜ |

---

## Tools (ADR-0030 outcome)

Tools ship as native capabilities, not MCP. Sequenced in
[TOOLS_STRATEGY.md](./TOOLS_STRATEGY.md); the ordering constraint is that nothing writes to
the outside world before it can be observed and approved.

| ID | Item | Size | Status |
|---|---|---|---|
| TL-1 | Remove dead `mcp.*` capabilities *(same as T6)* | S | 🔜 |
| TL-2 | Make `web.scrape` real using a fixed-domain search API, keeping the egress allowlist intact | M | ⬜ |
| TL-3 | Per-tool-call observability: which tool, which arguments, which result. Only `tool_calls` counts exist today | M | ⬜ |
| TL-4 | Tool-level approval (outbox row → `APPROVAL` node → deterministic send). `approval_risk` is currently never read at runtime | L | ⬜ |
| TL-5 | Messaging (telegram) — requires a new ADR superseding ADR-0004, plus TL-3 and TL-4 | L | ⬜ |

---

## Remaining open decisions

The five that blocked the most work are settled. What is left:

| ID | Decision | Blocks |
|---|---|---|
| D6 | Local model set — diagram versus code | SB-6b |
| D7 | Deployment target — Compose, or the unreferenced Kubernetes/Terraform definition | SB-3b |
| D8 | Signal taxonomy source once `SignalId` stops being a `Literal` | SB-1 |
| D9 | Fate of the remaining `planned` capabilities beyond `web.scrape` | TL-2 |
| D11 | Whether narrative claims rejected by the evidence gate should be repaired and retried rather than withheld | — |

---

## Suggested next block of work

1. **T10, T11, T6, T12** — small, and they close the gap between what the documents now say
   and what the code does. T10 in particular is a correctness fix: a citation that does not
   resolve undermines the product's central claim.
2. **SB-2** — the first change that alters what the product can do for a real customer.
3. **D8 → SB-1** — decouple the signal taxonomy. The single largest unlock for customer two.
4. **SB-3a, R6** — cheap durability and attack-surface wins that can ride alongside the above.
5. **SB-5+SB-4** — the orchestration change, now that ADR-0029 has scoped it.
6. **SB-6a** — model configuration persistence, which is worth doing before tiering because
   it fixes a live defect on its own.
