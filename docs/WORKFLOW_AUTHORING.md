# Workflow Authoring

How a workflow is designed in the console, what the editor can and cannot do, and which node
kinds actually do what their name says.

Written from driving the editor against a running stack on 29 July 2026, not from reading the
code. Where something is stated as a limit, it was observed. The UI is Turkish; its strings
are quoted as they appear.

**Read first:** `AGENTS.md`, `docs/IMPLEMENTATION_STATUS.md` (top section). For the execution
model behind this, ADR-0029.

---

## The one thing to know before you start

**There is no "new workflow" button.** The selector at the top of the editor lists workflows
that already exist; nothing in the interface creates an empty one. The only way to obtain a
new workflow id is **Şablon Yükle** — load a template, edit it, save it under the template's
id.

That is not a stylistic gap. It means the shape of what you can author is bounded by the five
templates, and it explains why the template path being broken (fixed 29 July 2026) made
authoring impossible rather than merely awkward.

---

## The screen

`#workflow` in the console. Four regions:

| Region | What it holds |
|---|---|
| **Top bar** | Workflow selector, draft/published badge, and the seven actions |
| **Left** | Node catalogue — 11 draggable kinds in five groups, with a search box (`Ara node…`) |
| **Centre** | The React Flow canvas: nodes, edges, zoom controls |
| **Right** | Node inspector — empty until you select a node (`Node seçin`) |
| **Footer** | Node count · validation state · current graph id and version · save state |

The seven actions, in the order you will use them:

| Button | Endpoint | Note |
|---|---|---|
| **Şablon Yükle** | `GET /api/workflows/templates` | The only route to a new workflow id |
| **Sürümler** | `GET /api/workflows/{id}/versions` | Version history; opening one loads it |
| **Kaydet** | `PUT /api/workflows/{id}/draft` | Requires the `analyst` role |
| **Dry-run** | `POST /api/workflows/dry-run` | |
| **Doğrula** | `POST /api/workflows/validate` | Runs the 14 rules below |
| **Yayınla** | save, then publish | Published versions are immutable (ADR-0008) |
| **Çalıştır** | `POST /api/workflows/{id}/run` | **Refuses unless the workflow is published** |

### The selector shows two entries with the same name

`builtin-growth-diagnostic` and `growth-diagnostic` both render as "Growth Diagnostic". You
cannot tell them apart in the dropdown. The footer is the only place the id is visible — read
it before you edit. Tracked as roadmap item T17.

---

## The authoring loop

1. **Şablon Yükle** → pick a template. The footer shows its id and `v1`.
2. Edit. Drag nodes from the catalogue, connect them, select a node to configure it.
3. **Doğrula.** The footer shows `Geçerli graph` or `N doğrulama hatası`. Before you press it
   the footer reads `Doğrulanmadı` — it does not claim validity it has not checked.
4. **Kaydet.** The footer shows `Taslak vN kaydedildi` and the workflow now appears in the
   selector.
5. **Yayınla** when it is right. This freezes the version.
6. **Çalıştır** — only works on a published version.

Steps 1–4 were verified end to end: loading `Lead Discovery & Signal Enrichment`, validating
it (200, valid), and saving it produced `lead-discovery-enrichment v1 draft` in
`GET /api/workflows`.

### What the inspector lets you change

For every node: the description (`Açıklama`). The node **ID is read-only**.

For an `agent_run` node, additionally:

- **Agent** — from the published agent registry, with its version
- **Model profili** — profiles unavailable in this installation are shown and disabled
- **Çıktı tipi** — `CompanyAnalysis`, `OpportunityHypotheses`, `EvidenceReview`, `OKFChangeSet`
- **Atanan Skill'ler** — capabilities. Ones with no handler behind them are disabled with a
  tooltip rather than assignable-but-inert.

Other node kinds have no configuration UI beyond the description, even where the runtime reads
config from them (`knowledge_search` needs `query`, `data_source_sync` needs `connector_id`,
`policy_check` needs `policy_id`). Those come from the template and cannot be edited in the
console.

---

## What the node kinds actually do

This is the part that most affects a workflow you author. Several nodes write a fixed string
into run state and complete — they are placeholders with real-sounding names.

| Node | What it does at runtime |
|---|---|
| `manual_trigger` / `schedule_trigger` / `onboarding_trigger` | Records which trigger fired |
| `data_source_sync` | Validates `connector_id`, then **always syncs the demo company regardless of it** (roadmap SB-2) |
| `normalize_context` | Writes the constant `"persisted-canonical-context"` |
| `okf_compile` | Writes the constant `"active-read-candidate-write"` |
| `knowledge_search` | **Echoes `config["query"]` into state. It does not search anything** (roadmap T11) |
| `deterministic_score` | Real — computes verified growth metrics and per-signal scores |
| `condition` | Real — evaluates the configured field/operator and branches |
| `policy_check` | Rejects any `policy_id` other than `material-claim-evidence`, then writes `"passed"` unconditionally |
| `agent_run` | Real — pinned agent version, model profile resolution, data-classification enforcement, scoped capability tools |
| `approval` | Real — sets the run to `awaiting_approval` and waits for a decision |
| `report_output` | Real, but **hardcoded to four agent results**: `company-analyst`, `growth-opportunity-analyst`, `evidence-reviewer`, `wiki-curator` |

Two consequences worth stating plainly:

- **A workflow whose graph passes validation can still be unable to run.** `report_output`
  reads all four agent results from state; a workflow with a different agent set raises when it
  reaches that node. This is why the four "executable" templates validate but do not complete
  (roadmap SB-2b).
- **Putting `knowledge_search` in a graph does not retrieve anything.** If your design depends
  on retrieval, it does not work yet.

---

## The 14 validation rules

`Doğrula` runs `apps/api/agi_server/workflow/validator.py`. The rules, by the code they
report:

| Code | Rule |
|---|---|
| `trigger.count` | Exactly one trigger node |
| `node.missing_config` | A node kind's required config keys are present |
| `condition.field` / `condition.operator` | A condition names a field and an allowed operator |
| `condition.branches` | A condition has both branches wired |
| `edge.unknown_node` | Every edge endpoint exists |
| `edge.source_type` / `edge.target_type` | Edge data types match what the nodes produce and accept |
| `edge.unexpected_branch` | Only conditions carry branch labels |
| `graph.cycle` | No cycles |
| `graph.unreachable` | Every node is reachable from the trigger |
| `output.missing` | At least one `report_output` |
| `approval.count` | Exactly one approval node for a published MVP workflow |
| `approval.order` | Approval sits after the work it gates |

The catalogue reference template (`Enterprise Account Expansion Blueprint`) is a useful probe:
it is deliberately incomplete and reports exactly three — `trigger.count`, `output.missing`,
`approval.count`.

---

## Which engine will run your workflow

**This is the sharpest limitation and nothing in the UI shows it.**

Engine selection is a hardcoded id set in `workflow/persistent_runtime.py`:

```python
workflow.id in {"builtin-growth-diagnostic", "growth-diagnostic"}
or workflow.id.startswith("qualification-")
```

Those run on the **LangGraph engine**. Everything else — including every workflow you author
from a template — runs on the **fallback runtime**, a separate topological executor with
different behaviour.

So `lead-discovery-enrichment`, saved and published, does not execute the way the built-in
diagnostic does, and the console gives no indication. ADR-0029 accepts that engine selection
must come from a property of the definition rather than an id set; until that lands, treat any
authored workflow as running on the second engine.

---

## Verified, and not

**Verified in a browser against a running stack:** template loading, validation of a valid
graph (200, `Geçerli graph`), validation of an invalid graph (200, `3 doğrulama hatası`), the
neutral pre-validation state, saving a template as a draft, and the draft appearing in
`GET /api/workflows`.

**Not verified:** publishing an authored workflow, running one, and what the fallback runtime
does with it. The node table above is read from the runtime source, not observed per node.
Anyone who takes that path should record what they find here.

## Known gaps, with roadmap ids

| Gap | Id |
|---|---|
| No way to create a workflow from scratch | — not yet tracked |
| Engine chosen by hardcoded id set | SB-5+SB-4 (ADR-0029) |
| `data_source_sync` ignores `connector_id` | SB-2 |
| Templates validate but cannot complete | SB-2b |
| `knowledge_search` retrieves nothing | T11 |
| Placeholder node kinds in the catalogue | N1 |
| Two selector entries render identically | T17 |
| Catalogue and nav buttons have no accessible name | T18 |
