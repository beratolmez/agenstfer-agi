# Capacity and Quota

Fills the capacity-policy clause left open in ADR-0012. Figures marked **measured** were
observed on 28 July 2026 running the built-in diagnostic against live Gemini models; the rest
are read from configuration and are marked accordingly.

---

## What one diagnostic costs

The `builtin-growth-diagnostic` workflow has 12 nodes, four of which call a model.

| Agent | Output contract | Output budget | Measured need |
|---|---|---|---|
| `company-analyst` v4 | `CompanyAnalysis` | 900 | ~760 tokens |
| `growth-opportunity-analyst` v4 | `OpportunityHypotheses` | 2000 | **1357 tokens** (measured against the real 8.8 KB prompt) |
| `evidence-reviewer` v3 | `EvidenceReview` | 1800 | varies with claim count; batched |
| `wiki-curator` v3 | `OKFChangeSet` | 1200 | ~500 tokens |

**Provider requests per run: 4 minimum.** The evidence reviewer batches claims
(`diagnostics/service.py:144-162`, 5 claims or 6 distinct evidence IDs per batch), so a run
with many material claims issues more than one reviewer request. A realistic run is
**4–7 requests**.

Retries are deliberately not multiplied: the provider client is configured for a single
attempt (`HttpRetryOptions(attempts=1)` for Gemini, `max_retries=0` for OpenAI-compatible
providers), and only the agent layer retries. Before ADR-0026 the two layers compounded and a
single node could consume nine requests.

---

## Gemini free tier

**This is the binding constraint for demos.** Measured on the free tier:

| Limit | Value | Consequence |
|---|---|---|
| Requests per day, per model | **20** | About **three to five diagnostics per day per model** |
| Requests per minute, per model | provider-enforced | Back-to-back runs can hit 429 |
| `gemini-2.0-flash` on this key | quota **0** | Model unusable; do not select it |
| `gemini-2.5-flash-lite` | 404 for new users | Retired |

Quota resets on Google's schedule, not local midnight. A 429 surfaces as an actionable
message rather than a generic failure (`agents/runtime.py:246-250`).

**Planning rule for a demo:** budget one model per demo run and verify quota beforehand. If a
run must not fail, use a paid project or a locally hosted model.

### Model selection notes

Thinking tokens are billed against the same output budget as visible output, so an unbounded
Gemini 3.x call spends its entire budget on hidden reasoning and returns truncated JSON. The
gateway therefore pins `thinking_level: MINIMAL` for the 3.x family and `thinking_budget: 0`
for 2.x (`model_gateway.py:151-157`). `reasoning_effort: "none"` is rejected by Gemini with
HTTP 400 and must not be carried over from the Ollama path.

Gemini 3.x also requires `thought_signature` to be echoed on every follow-up tool turn, which
the OpenAI-compatibility shim drops — hence the native transport (ADR-0026).

### Routing Gemini through an aggregator re-introduces that bug

`NATIVE_CLOUD_PROVIDERS = {"gemini"}` in `agents/model_gateway.py`. Only the direct Gemini
provider uses the native transport; every other provider, including OpenRouter, goes through
`OpenAIChatModel`. **A Gemini 3.x model reached via OpenRouter therefore drops
`thought_signature` again and fails with HTTP 400 on the first parallel tool call** — the same
defect ADR-0026 fixed.

Use OpenRouter for non-Gemini families (Qwen, DeepSeek, Llama, Mistral), which have no such
requirement, and call Gemini directly. Egress is already prepared: `.openrouter.ai` is in the
Squid allowlist. If Gemini must be routed through an aggregator, the native path has to be
extended to that provider first.

Measured on this codebase, not inferred: asked for one tool call with
`parallel_tool_calls: false`, Gemini returned three and the follow-up turn without the
signature returned 400; with the signature preserved it returned 200.

---

## Timeouts

| Scope | Value | Source |
|---|---|---|
| `company-analyst` | 300 s | spec |
| `growth-opportunity-analyst` | 360 s | spec |
| `evidence-reviewer` | 420 s | spec |
| `wiki-curator` | 300 s | spec |
| Agent execution wrapper | `spec.timeout_seconds` | `agents/runtime.py:242` |
| Scheduler tick | every 30 s | `scheduler.py` |
| Approval expiry | 7 days | `workflow/default.py` (`timeout_days`) |
| Health check probes | 5 s interval, 3 s timeout, 20 retries | `docker-compose.yml` |

`nginx` does **not** set `proxy_read_timeout`, so the default of 60 s applies. This is safe
today because `/api/diagnostics/run` returns immediately with a `run_id` and the client polls;
it would break again if run execution ever became synchronous.

---

## Concurrency

**Current supported concurrency: one diagnostic at a time.** This is a property of the
implementation, not a tuned limit:

- Workflow execution runs on the API event loop via `asyncio.create_task`
  (`persistent_runtime.py:690`), with synchronous SQLAlchemy I/O and model calls inside it.
  A long agent call therefore delays other API requests.
- The returned task reference is not retained, so CPython may collect a background run
  mid-flight.
- The scheduler shares the same loop and ticks every 30 s.

Roadmap items SB-3a and SB-3b address both. Until they land, treat concurrent diagnostics as
unsupported and size the deployment for a single active run.

---

## Storage

| Store | Growth driver | Notes |
|---|---|---|
| `postgres_data` | runs, step runs, evidence items, audit events | Audit and step rows grow per run; no retention policy defined yet |
| `knowledge_data` | raw vault + OKF bundle + candidates | Raw snapshots are immutable and never pruned by design |
| `qmd_data` | derived retrieval index | Disposable; rebuildable from the active bundle |

No retention or archival policy exists for any of these. That gap belongs with the
data-retention decision in `THREAT_MODEL.md`.

---

## Model tiering (not yet implemented)

The intended model is per-customer and per-agent low / mid / high profiles with Langfuse
tracing, usage limits and billing hooks. Today `PROFILES` holds two fixed local entries plus
one synthetic cloud profile (`model_gateway.py:17-33`), and there is no usage accounting
beyond per-run token totals persisted on `WorkflowRun.token_usage`.

Tracked as SB-6 and decision D10 in [REMEDIATION_ROADMAP.md](./REMEDIATION_ROADMAP.md).
