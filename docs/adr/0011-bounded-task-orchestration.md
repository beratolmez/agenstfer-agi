# ADR-0011: Bounded task and round orchestration

## Status

Accepted for post-MVP — 17 July 2026

## Context

The team is considering an orchestration agent that converts a user goal into worker tasks, chooses a
bounded number of workers, executes them in rounds, and continues unresolved work until completion or
a round limit. This is useful for knowledge-gap resolution but conflicts with the MVP's deterministic
workflow and evidence gates if it is left open-ended.

## Decision

The MVP Growth Diagnostic remains a fixed, versioned workflow with four typed agents. A later
`BoundedTaskOrchestrator` may propose a typed `TaskPlan`, but runtime policy controls worker profiles,
capabilities, classification, maximum workers, maximum rounds, timeout, token/cost budget, and
completion criteria. DBOS persists each task and round; a typed evaluator returns `complete`,
`continue`, `blocked`, `needs_human_approval`, or `budget_exceeded`.

Workers are selected from a code-defined registry. They cannot create arbitrary workers, expand their
tools, execute user code, call unallowlisted MCP servers, or perform external writes. Candidate OKF
changes and material report outputs still require evidence review and the existing approval lifecycle.

## Consequences

- Dynamic planning is possible without turning the product into an uncontrolled agent swarm.
- Parallel fan-out can be added later only for independent read-only tasks with deterministic join,
  resource limits, and restart/idempotency coverage.
- The feature requires a separate golden evaluation, budget, prompt-injection, unsupported-claim,
  and recovery gate before it can replace or extend a supported workflow.

