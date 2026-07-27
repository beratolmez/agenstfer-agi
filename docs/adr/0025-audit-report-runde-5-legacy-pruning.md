# ADR-0025: Audit Report Runde 5 — Legacy Package Pruning (LO-04, LO-05, LO-06)

## Status
Accepted

## Date
2026-07-27

## Context

The second Audit Findings report (Audit Round: Low-priority blockers LO-04, LO-05, LO-06)
identified three residual issues in the unintegrated legacy microservice
`apps/services/ai-agent`:

1. **LO-04** — `ai_agent/models.py` contained a silent `TestModel()` fallback that
   created a second ungoverned LLM inference path bypassing Model Gateway policy
   (cloud opt-in, data classification, audit logging — ADR-0006, ADR-0016).
   Note: the direct `GEMINI_API_KEY` read referenced in the audit had already been
   replaced by a `get_settings()` call; the critical remaining defect was the
   unconditional `except Exception: pass → return TestModel()` that swallowed all
   gateway errors silently.

2. **LO-05** — `ai_agent/tools/web_scraper.py` was a stub that returned a synthetic
   bounded-evidence string. Although it did not make real HTTP calls at the time of
   audit, the original version at the time of the finding *did* make direct outbound
   HTTP with no egress/policy control. The stub still needed to be replaced with an
   explicit `NotImplementedError` guard to prevent any future restoration of the
   ungoverned path (ADR-0016 Phase 5 "pruning" decision).

3. **LO-06** — `apps/api/agi_server/workflow/runtime.py:13` contained a stale DBOS-era
   docstring ("DBOS step wrapper checkpoints each return value") that was orphaned after
   the DBOS removal in Phase 20 / ADR-0022. The `durable_persisted_workflow` function
   referenced in the audit no longer exists in `persistent_runtime.py`; the only
   remaining DBOS artefact was this docstring.

## Decision

### LO-04 — ai_agent/models.py
- Remove the `try/except Exception: pass → return TestModel()` pattern.
- The function now explicitly raises `RuntimeError` when the Model Gateway is
  unreachable or when no suitable Pydantic AI model class can be resolved for the
  profile, making failures visible and preventing ungoverned inference.
- The module-level docstring is updated to clearly state that all production
  inference must go through `apps/api/agi_server/agents/runtime.py`.
- Direct `GEMINI_API_KEY` environment variable reads (already removed in the
  working copy at audit time) are confirmed absent.

### LO-05 — ai_agent/tools/web_scraper.py
- Replace the synthetic "bounded evidence excerpt" stub with a function that raises
  `NotImplementedError` explicitly, documenting the pruning decision and the correct
  implementation path (agi_server capability registry + egress-gateway proxy).
- The module-level docstring records the ADR-0016 Phase 5 pruning decision and links
  to the ADR-0005 egress boundary.

### LO-06 — workflow/runtime.py DBOS docstring
- Replace `"""Deterministic node dispatcher; DBOS step wrapper checkpoints each return value."""`
  with `"""Deterministic node dispatcher for dry-run / visual-editor execution paths."""`.
- This removes the last textual reference to the DBOS execution model from the active
  codebase. All DBOS scripts were removed in ADR-0022; this docstring was the sole
  remaining artefact.
- ADR-0022 is superseded in this specific respect: its "Repository is free of … deprecated
  DBOS scripts" claim is now also true of DBOS documentation artefacts in source files.

## Consequences

- `ai_agent/models.py` no longer provides a silent fallback path to unauthenticated or
  ungoverned model inference. Failures in the legacy service are now loud and traceable.
- `web_scraper.py` cannot be accidentally re-activated with a trivial code change; any
  real web scraping implementation must go through the capability registry and egress proxy.
- The codebase contains zero DBOS textual artefacts in active source files (scripts were
  removed in ADR-0022; the docstring is removed here).
- The legacy `apps/services/ai-agent` package remains classified as an unintegrated legacy
  microservice (`IMPLEMENTATION_STATUS.md` §4, item 5); these changes do not change its
  integration status, only reduce its risk surface.
