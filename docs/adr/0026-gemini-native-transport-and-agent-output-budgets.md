# ADR-0026: Gemini Native Transport, Bounded Reasoning, and Agent Output Budgets

- **Status:** Accepted
- **Date:** 28 July 2026
- **Supersedes:** the Gemini portions of ADR-0017 (OpenAI-compatible Bearer transport) and the
  `parallel_tool_calls` mitigation introduced for AUDIT_FINDINGS BLK-05.

## Context

The `builtin-growth-diagnostic` workflow could not complete a single run against a Gemini
provider. Four independent defects were reproduced against the live Gemini API:

1. **`thought_signature` round-trip.** Gemini 3.x requires the per-call `thought_signature` to be
   echoed back on every follow-up tool turn. The OpenAI-compatibility endpoint returns it inside
   `extra_content.google.thought_signature`, but `OpenAIChatModel` does not carry that
   provider-specific field back. Measured directly: a turn with three parallel tool calls returns
   `200`; replaying it with the signature stripped returns `400 INVALID_ARGUMENT`, and replaying it
   with the signature preserved returns `200`. Every diagnostic agent injects tools, so the run
   failed at the first tool round-trip.
2. **`parallel_tool_calls` is not honoured.** The earlier mitigation set
   `parallel_tool_calls: False`. The setting is valid in Pydantic AI and is transmitted, but Gemini
   ignores it: asked for one tool call, it returned three. The mitigation never worked.
3. **Unbounded reasoning inside the output budget.** Gemini bills hidden reasoning against the same
   budget as visible output. A real `CompanyAnalysis` extraction at `max_tokens=900` produced
   `finish_reason: length` with 31 visible tokens and 865 reasoning tokens, so the JSON was
   truncated and structured-output validation failed.
4. **Output budgets set below the contract's real cost.** `growth-opportunity-analyst` must emit
   exactly five hypotheses with Turkish rationales. Measured need against the real workflow prompt
   (8.8 KB): **1357 output tokens**. Its spec allowed 900, so the JSON was cut mid-string.

Two further defects made these effectively undiagnosable: `logger.exception` output never reached
stdout, and the `wiki-curator` path rule (`reports/*.md`) was enforced by the runtime but never
stated in the agent's prompt.

## Decision

1. **Gemini uses the native `google-genai` transport.** `NATIVE_CLOUD_PROVIDERS = {"gemini"}`
   selects `GoogleModel` + `GoogleProvider`; other cloud providers keep the OpenAI-compatible
   client. The native transport round-trips `thought_signature`, so multi-turn tool use works.
   `parallel_tool_calls` is removed as a Gemini mitigation because it is not honoured.
2. **Reasoning is bounded explicitly per model family.** Gemini 3.x receives
   `google_thinking_config={"thinking_level": "MINIMAL"}` (3.x cannot disable thinking);
   Gemini 2.x receives `{"thinking_budget": 0}`. Note `reasoning_effort: "none"` is rejected by
   Gemini with HTTP 400 and must not be reused from the Ollama path.
3. **Provider retries are disabled; the agent layer owns retry.** `HttpRetryOptions(attempts=1)`
   on the Google client mirrors `max_retries=0` on the OpenAI client, so one diagnostic cannot
   silently multiply into an entire free-tier daily quota.
4. **Agent output budgets are set from measurement, and specs are versioned when changed.**
   `growth-opportunity-analyst` v3 → **v4** with `max_output_tokens: 2000`.
   `company-analyst` v3 → **v4** and `wiki-curator` v2 → **v3** for prompt-contract changes.
   `build_default_workflow` pins the new versions, per ADR-0008.
5. **Agent prompts state the constraints the runtime actually enforces.** `wiki-curator` now
   states the `reports/*.md` rule with an example; the rejection error names the offending paths
   instead of reporting a generic "outside reports/".
6. **Claims must cite all directly supporting evidence.** `company-analyst` previously required
   "at most one evidence ID per claim" while the evidence gate demanded that the cited evidence be
   sufficient — an internal contradiction that guaranteed rejection of aggregate claims. Analysts
   now cite every supporting ID and are forbidden from asserting counts, ratios, or totals that do
   not appear verbatim in a cited excerpt.
7. **The control-plane logger is configured at startup.** `configure_logging()` attaches a stdout
   handler, and Alembic's `fileConfig` is called with `disable_existing_loggers=False` so it no
   longer tears that logger down during migrations.

## Consequences

- The diagnostic now advances through 10 of 11 nodes against a live Gemini model: ingestion,
  knowledge, `company-analyst`, `growth-opportunity-analyst`, deterministic scoring,
  `evidence-reviewer` and `wiki-curator` all complete.
- Failures are now diagnosable: full tracebacks reach stdout and `error_json` carries provider,
  model, profile, HTTP status and node id.
- `apps/services/ai-agent` is unaffected; it remains unintegrated legacy code.
- **Open item.** The run still stops at the evidence gate: the reviewer judges the analysts'
  hypothesis rationales unsupported by the demo dataset's evidence, and the gate is all-or-nothing
  (`if failures or not review.approved: raise`). Tightening the analyst prompts reduced but did not
  eliminate rejections. Whether the gate should keep failing the whole run, or instead exclude
  unsupported claims and surface them as data gaps (PRD 6.2 "eksik veri uyarıları"), is a product
  decision recorded in AUDIT_FINDINGS Tur 3 and deliberately left open here.

## Verification

- `uv run pytest apps/api/tests/` — full suite green, including three previously failing tests
  (LangGraph checkpointer `thread_id`, probe nonce liveness, evidence-gate fail-open).
- Live Gemini run: `company-analyst` returns a schema-valid `CompanyAnalysis` with bound evidence
  IDs over a two-request tool round-trip.
- `test_gemini_uses_native_transport_with_retries_disabled` asserts `GoogleModel` and
  `attempts == 1`; `test_gemini_reasoning_and_tool_settings` and
  `test_gemini_2x_uses_numeric_thinking_budget` pin the thinking configuration per family.
