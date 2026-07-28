# ADR-0028: Silent Failure Fixes and Repository Pruning

- **Status:** Accepted
- **Date:** 28 July 2026
- **Supersedes:** the "repository is free of deprecated artefacts" claim in ADR-0022 and
  ADR-0025, both of which were made while `apps/services/*` and the `apps/api/main.py` shim
  were still present.

## Context

The architecture assessment (`docs/ARCHITECTURE_ASSESSMENT.md`) found three defects that
failed without producing any signal, and a body of dead code that made the repository
misrepresent itself.

The three defects shared a cause: nothing observed the failing path.

1. `scheduler_loop` had no `try/except`. One database error ended the task, so every
   schedule and every queued event stopped being processed for the rest of the process
   lifetime — and the exception only surfaced at shutdown.
2. The fallback runtime read `active_step.node_id`; the column is `step_id`. The error
   handler therefore raised `AttributeError` inside itself: the original failure was lost,
   `error_json` was never written, and the run stayed `running` forever.
3. `/api/sources/test-mcp` queried `MCPProfile.server_url`; the column is `server_identity`.
   Every real request returned 500. The one test passed `db=None` and never entered that
   branch.

Separately, the repository contained a second FastAPI entry point that shadowed real
endpoints but was never served, two legacy microservice packages that no production code
imported and whose dependencies were not even installed, fourteen empty scaffold
directories, a dead second orchestrator, and several scripts pointing at files that no
longer exist.

## Decision

**1. Fix the three defects and cover each with a regression test that fails against the old
code.** `scheduler_loop` now guards each tick and logs the failure while continuing;
`CancelledError` still propagates so shutdown is unaffected.

**2. Delete code that no production path reaches.** Removed: `apps/api/main.py` and its
test, `apps/services/ai-agent`, `apps/services/rag`, fourteen empty `.gitkeep`
directories, `run_growth_diagnostic` with its four exclusive helpers, the
`build_langgraph_workflow` / `LangGraphWorkflowRuntime` stub, `StructuredOutputProbe`,
`list_capabilities()`, and five unreferenced or broken scripts.

**3. Preserve coverage rather than delete it with the code.** The five business-domain
contracts (competitor, security, financial, SEO, CSAT) are PRD targets that no agent spec
can select yet, so their schema tests were kept and stripped of the legacy dependency. The
artifact, step-sequence and idempotency assertions that only existed against the dead
orchestrator were ported to the production LangGraph path. The two evidence-gate tests now
call `_enforce_evidence_gate` directly, which is what production uses.

**4. Repair or expose broken scripts.** DBOS references removed from `backup.sh` and
`restore.sh` (the `_dbos_sys` database no longer exists, and `backup.ps1` had already
diverged); the nonexistent `--profile cloud` dropped from `release-rehearsal.sh`. The
model-qualification harness was built on the removed legacy stack and never shipped inside
the image, so it has not run for some time — `qualify-model.*` now fails with an explicit
message instead of a missing-file error. A release gate that silently does nothing is worse
than one that is visibly absent.

**5. Correct documents that claimed capabilities the code does not have.**
`IMPLEMENTATION_STATUS.md` marked ChromaDB retrieval and the MCP gateway as active; both are
now `[~]` with the actual scope stated. `DOMAIN_CONTRACTS.md` claimed a PostgreSQL
checkpointer and `interrupt_before`/`interrupt_after`; neither is used.

## Consequences

- The repository no longer contains application code outside `apps/api/agi_server` and
  `apps/web`.
- A failed run now records why it failed; a failed scheduler tick no longer stops the
  scheduler.
- Test count moves from 173 to 165: eight tests were removed with the code they covered, and
  their unique assertions were ported rather than dropped.
- `qualify-model.*` now fails by design. The harness must be rebuilt on
  `agi_server.evaluation` so that it ships in the image — tracked as T4 in
  `docs/REMEDIATION_ROADMAP.md`.
- ADR-0002 and ADR-0011 remain gutted "DELETED" stubs with no superseding pointer, and ADR
  number 4 is still used by two files. Both are traceability debt, left as-is because
  renumbering an accepted ADR is worse than the inconsistency.

## Verification

- `uv run ruff check apps/api` — clean
- `uv run pytest apps/api/tests/` — 165 passed
- Reverting the `step_id` fix makes `test_failed_run_records_error_instead_of_staying_running`
  fail with the original `AttributeError`, confirming the test is not vacuous
- Live end-to-end diagnostic still completes: 12/12 nodes → approval → `completed`
