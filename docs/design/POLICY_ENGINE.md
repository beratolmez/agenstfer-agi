# Policy Engine — Design Skeleton

**Status:** Not implemented. This is a scoping document, not a specification.
**Source requirement:** PRD §6.3, listed in PRD §19 as one of the four core components.

This document exists because the Policy Engine had no design record at all — neither code nor
ADR. It states what exists today, what the PRD asks for, and the decisions that must be made
before anything is built. It deliberately does not invent a schema.

---

## What exists today

There is no policy engine. The `policy_check` node accepts exactly one policy ID and then
writes `"passed"` without evaluating anything:

```python
elif node.kind == NodeKind.POLICY_CHECK:
    if node.config["policy_id"] != "material-claim-evidence":
        raise ValueError("Policy is not allowlisted")
    result.setdefault("policy_checks", {})[node.id] = "passed"
```
`workflow/persistent_runtime.py:291-294`

The node is offered in the catalogue (`catalog.py`) and the Workflow Editor, so a user can add
a policy gate that does nothing.

Several primitives that a policy engine would build on **do** exist and work:

| Primitive | Location |
|---|---|
| Role-based access control (flat, three roles) | `security.py:169-177` |
| Data classification boundary, fail-closed for cloud | `agents/runtime.py:78-85` |
| Capability allowlist, narrowing-only | `agents/runtime.py:184-207` |
| Approval gate with risk field on the agent spec (`approval_risk`) | `registry.py`, `persistent_runtime.py` |
| Evidence gate (tiered) | `diagnostics/service.py:405-456` |
| Audit trail | `security.py` (`record_audit`), `audit_events` table |

So the raw material is present; what is missing is a rule model that composes it and a
decision point that consults it.

---

## What the PRD asks for

PRD §6.3 lists twelve dimensions. Mapping them against today:

| Dimension | Today |
|---|---|
| Channel permission rules | No channels exist — MVP is read-only (ADR-0004) |
| User role and authority level | Flat RBAC, three roles, no hierarchy |
| Agent authority limits | Capability allowlist only |
| Consent state | Nothing (see `CONSENT_LEDGER.md`) |
| Opt-out state | Nothing |
| Do-not-call state | Nothing |
| Data sensitivity level | `DataClassification`, enforced at the model boundary |
| Platform usage rules | Nothing |
| Country/region commercial communication rules | Nothing |
| Risk classification | `approval_risk` on the agent spec; not evaluated at run time |
| Approval requirement | One approval kind, `okf-candidate-merge` |
| Action limit | Nothing |

Six of twelve have no representation at all, and four of the remaining six exist as static
declarations rather than evaluated policy.

---

## Open decisions

These must be answered before implementation, and several are product decisions rather than
engineering ones.

1. **Scope for the first version.** The MVP is read-only toward external systems (ADR-0004),
   so channel permissions, consent and do-not-call have nothing to gate yet. Is the first
   Policy Engine about *data access* (which agent may read which classification from which
   source) rather than *actions*? That version is buildable now and has immediate value;
   the action-gating version has no actions to gate.

2. **Rule authorship.** Code-defined and versioned like capabilities, or
   administrator-editable data? AGENTS.md requires that agent tools and workflow nodes come
   from code-defined allowlists and forbids executing user-supplied code. An
   administrator-editable rule language is not obviously in scope of that prohibition, but it
   is close enough to need an explicit decision.

3. **Evaluation point.** A policy that only runs at a `policy_check` node can be bypassed by
   omitting the node. Alternatives: evaluate inside `_execute_node` for every node, or at the
   capability-tool boundary in `ScopedCapabilityTools`. The tool boundary is the only place
   that cannot be routed around by workflow authoring.

4. **Decision outcomes.** Binary allow/deny, or allow / deny / require-approval? The latter
   integrates with the existing Approval Center but needs a second approval `kind`.

5. **Failure mode.** Fail-closed is consistent with the rest of the system (cloud opt-in,
   evidence gate, capability allowlist). Confirm that a policy evaluation error stops the run
   rather than defaulting to allow.

6. **Violation record.** PRD §13 lists `policy violation attempt` as an observability metric.
   Does a denied action produce an audit event, and is it surfaced in the compliance dashboard
   described in PRD §5.5?

---

## Suggested first slice

If a minimal version is wanted before the broader questions are settled: make `policy_check`
actually evaluate the one policy it already claims to enforce. `material-claim-evidence` has a
real implementation sitting next to it — `_enforce_evidence_gate` — and wiring the node to it
would turn a decorative gate into a working one without deciding anything on this list.

Anything beyond that should wait for decisions 1–3.

---

## Related

- `docs/design/CONSENT_LEDGER.md` — the missing input for six of the twelve dimensions
- ADR-0004 — no external write in MVP, which bounds what there is to gate
- ADR-0032 — tenancy, which determines whether policy is installation-scoped
