# ADR-0033: Model Tiering and Usage Governance

- **Status:** Proposed — decision required
- **Date:** 28 July 2026
- **Blocks:** SB-6 in `docs/REMEDIATION_ROADMAP.md`
- **Relates to:** ADR-0003 (local-first policy), ADR-0006 (cloud opt-in), ADR-0010
  (Langfuse boundary), ADR-0026 (native Gemini transport)

## Context

The intended direction is per-customer and per-agent model selection at low / mid / high
tiers, with Langfuse tracing, usage limits and billing hooks. The current gateway cannot
express any of that.

**What exists** (`model_gateway.py:17-33`):

- `PROFILES` — two hardcoded local entries, `local-balanced` (`qwen3.5:9b`) and
  `local-strong` (`qwen3.5:27b`)
- `CLOUD_PROVIDERS` — four provider base URLs with a default model each
- `cloud-balanced` is not a profile at all; it is synthesised at resolve time into
  `cloud-<provider>` from three global settings (`cloud_provider`, `cloud_model`,
  `cloud_api_key`)

The consequences:

- **Tier is not a concept.** An agent spec picks one of three literal profile names
  (`registry.py:18`). There is no notion that a classification task should use a cheap model
  and a strategy synthesis an expensive one.
- **Configuration is global, not per-customer or per-agent.** One cloud provider and one
  cloud model for the entire installation.
- **Usage is recorded but not governed.** `WorkflowRun.token_usage` aggregates per run; no
  budget, no limit, no rejection path when a limit is exceeded.
- **The model set does not match the plan.** The manager's diagram names GLM 5.2 and
  QWEN 3.7 Max; the code pins `qwen3.5:9b/27b`. Nobody has reconciled these.
- **Langfuse is not wired.** ADR-0010 defines the boundary; `observability.py` emits HTTP
  request spans only — no agent decision traces, no model response traces, no per-agent cost
  attribution.

Note the free-tier constraint measured in `CAPACITY_AND_QUOTA.md`: 20 requests per day per
model, against 4–7 requests per diagnostic. Quota governance is not a future nicety; it is
already the binding limit on how often the product can be demonstrated.

## Decisions required

1. **Tier vocabulary.** Fix a small closed set — `low` / `standard` / `high` — and make agent
   specs declare a *tier* rather than a concrete profile, with the tier resolved to a model at
   run time from installation configuration. This is what decouples "what this agent needs"
   from "what this customer bought".
2. **Configuration scope.** Where does the mapping live — installation-wide, per agent, or
   both with agent overriding installation? Given ADR-0032's deployment-level tenancy, the
   natural home is a persisted installation-scoped table, with an optional per-agent override.
3. **Persistence.** The cloud API key currently lives only in the in-memory `Settings`
   singleton, so any provider configuration entered at onboarding is lost on restart while
   `setup_completed` stays `true`. Tiering makes this worse, since there will be several
   mappings to lose. Persistence must be solved as part of this work.
4. **Enforcement point.** Where is a budget checked — before `run_managed_agent`, or inside
   `resolve_model_profile`? A pre-flight check that can reject a run before spending a request
   is the only version that helps with a 20/day quota.
5. **Langfuse boundary.** ADR-0010 forbids sending prompts, source bodies, evidence excerpts,
   secrets and contact identifiers. Tiering needs per-agent cost and latency attribution,
   which is content-safe metadata and fits within that boundary — but the tracing integration
   has to be written to respect it rather than defaulting to full payload capture.
6. **Local model set.** Reconcile the diagram (GLM 5.2, QWEN 3.7 Max) with the code
   (`qwen3.5:9b/27b`), and decide which local models each tier maps to.

## Recommendation

Sequence this after ADR-0032, and split it:

- **Step 1 — persistence.** Move provider, model and encrypted key out of the in-memory
  singleton into the database. This is a prerequisite for everything else and independently
  fixes a real defect.
- **Step 2 — tier indirection.** Introduce the tier vocabulary and the tier → profile
  resolution table. Agent specs migrate from a literal profile to a tier; a spec version bump
  handles the transition under ADR-0008.
- **Step 3 — governance.** Budgets, pre-flight rejection, and Langfuse attribution.

Do not build billing before step 3: without usage attribution there is nothing to bill from.

## Consequences of not deciding

Every customer installation runs one global model for every task regardless of cost or
sensitivity, provider configuration is lost on restart, and free-tier quota exhaustion
continues to surface as a mid-run failure rather than a pre-flight refusal.
