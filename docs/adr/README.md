# Architecture Decision Records

Every durable architectural decision lives in this folder. There is no other place. If you
cannot find the reason for something here, it was never decided — and that is itself useful
information.

**Do not read all 34.** Read the ones your task touches, from the first table below.

---

## Load-bearing today

These constrain current work. Cite them; do not contradict them without a superseding ADR.

| ADR | Decision | Read when |
|---|---|---|
| [0001](./0001-okf-postgresql-boundary.md) | OKF and PostgreSQL ownership boundary | Touching knowledge storage or persistence |
| [0004](./0004-no-external-write-in-mvp.md) | **No external write in MVP** | Adding any outbound capability — this is the gate |
| [0005](./0005-ingress-and-network-boundaries.md) | Ingress/egress boundaries and the allowlist | Network, scraping, or provider connectivity |
| [0007](./0007-okf-candidate-lifecycle.md) | Approval-controlled OKF candidate lifecycle | Anything that changes the active knowledge bundle |
| [0008](./0008-versioned-agent-policy-and-publication.md) | Versioned, immutable agent and workflow definitions | Editing an agent spec or workflow definition |
| [0026](./0026-gemini-native-transport-and-agent-output-budgets.md) | Gemini native transport, bounded reasoning, measured budgets | Model gateway or provider work |
| [0027](./0027-tiered-evidence-gate.md) | Tiered evidence gate — deterministic blocks, narrative withheld | Diagnostics, claims, or evidence handling |
| [0029](./0029-langgraph-execution-depth.md) | LangGraph depth: checkpointer + interrupts, one engine | Workflow execution or orchestration |
| [0030](./0030-mcp-status.md) | MCP is a target specification; tools ship native | Agent tools or capabilities |
| [0031](./0031-okf-wiki-and-vector-retrieval.md) | Wiki and vector are one retrieval layer, two paths | Retrieval, search, or citation resolution |
| [0032](./0032-tenancy-model.md) | Single-tenant; isolation by deployment separation | Anything touching customers or data boundaries |
| [0033](./0033-model-tiering-and-usage-governance.md) | Model tiering, staged: persistence → tiers → governance | Model selection or cost work |

Also relevant, less often: [0003](./0003-local-first-model-policy.md) local-first models ·
[0006](./0006-opt-in-cloud-model-governance.md) cloud opt-in ·
[0009](./0009-productized-customer-deployment.md) deployment model ·
[0010](./0010-langfuse-observability-boundary.md) observability boundary ·
[0012](./0012-aws-local-gpu-network-boundary.md) inference boundary ·
[0013](./0013-web-ui-ux-design-decisions.md) UI conventions ·
[0016](./0016-unified-runtime-migration.md) runtime target ·
[0034](./0034-unified-onboarding-and-dynamic-model-discovery.md) onboarding flow.

## Change logs, not decisions

[0017](./0017-model-gateway-and-onboarding-fix.md),
[0018](./0018-docker-network-egress-and-setup-completion.md),
[0019](./0019-audit-report-runde-1-critical-fixes.md)–[0025](./0025-audit-report-runde-5-legacy-pruning.md),
[0028](./0028-silent-failure-fixes-and-repository-pruning.md) record what was fixed in a given
round rather than a decision with alternatives. Read one only to answer "was this specific
thing already fixed, and how". Their conclusions are already reflected in
[IMPLEMENTATION_STATUS.md](../IMPLEMENTATION_STATUS.md).

Note that several of these claim full resolution of an audit round; the audit that followed
found otherwise. Trust `IMPLEMENTATION_STATUS.md` over an ADR's self-assessment.

## Broken references

[0002](./0002-pydantic-ai-dbos.md) and [0011](./0011-bounded-task-orchestration.md) were
emptied to the single word `DELETED` with no pointer to what replaced them. Their subjects —
the agent framework and task orchestration — are now covered by
[0016](./0016-unified-runtime-migration.md) and [0029](./0029-langgraph-execution-depth.md).
Do not read their absence as a decision to remove the capability.

[0034](./0034-unified-onboarding-and-dynamic-model-discovery.md) was numbered `ADR-004` until
29 July 2026, colliding with [0004](./0004-no-external-write-in-mvp.md). References to
"ADR-004" in `docs/AUDIT_FINDINGS.md` mean the onboarding document.

---

## Writing one

Copy the shape of [0029](./0029-langgraph-execution-depth.md):

**Status** · **Date** · what it supersedes or relates to · **Context** with `file:line`
evidence · **Options** with their costs · **Decision** · **Consequences** · **Verification**.

Rules:

- Number sequentially from the highest existing number. Filename `NNNN-kebab-title.md`, and
  the `# ADR-NNNN:` heading must match the filename.
- Context cites code, not impressions. An ADR whose context cannot be checked cannot be
  re-evaluated later.
- Record the options you rejected and why. The rejected option is the part a future reader
  needs; the chosen one is visible in the code.
- **Status is `Proposed` until a human approves it. Never mark your own ADR `Accepted`.**
- Superseding an ADR means editing the old one to say so and link forward. Never delete an
  ADR — [0002](./0002-pydantic-ai-dbos.md) is what that costs.
