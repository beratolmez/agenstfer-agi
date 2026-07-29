# Documentation Map

Start with **[AI_DEVELOPMENT_GUIDE.md](./AI_DEVELOPMENT_GUIDE.md)**. It tells you which of
these to read for the task in front of you, and which to skip. This page is the inventory;
the guide is the route.

Engineering documents and ADRs are English. Stakeholder-facing documents are Turkish.

---

## Living documents — kept true to the code

| Document | Answers |
|---|---|
| [AI_DEVELOPMENT_GUIDE.md](./AI_DEVELOPMENT_GUIDE.md) | How do I work in this repository? What must I read, and what does "done" mean? |
| [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md) | What actually works today, versus what is only specified? |
| [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md) | What is the stack and the topology? |
| [DOMAIN_CONTRACTS.md](./DOMAIN_CONTRACTS.md) | What does each term mean, and which store owns it? |
| [REMEDIATION_ROADMAP.md](./REMEDIATION_ROADMAP.md) | What is left to do, in what order, and what is still undecided? |
| [API_REFERENCE.md](./API_REFERENCE.md) | What endpoints exist, and which role does each need? |
| [SECURITY_CONTROLS.md](./SECURITY_CONTROLS.md) | Which control is enforced by which code, and proven by which test? |
| [CAPACITY_AND_QUOTA.md](./CAPACITY_AND_QUOTA.md) | What does a run cost, what are the limits, what concurrency is supported? |
| [THREAT_MODEL.md](./THREAT_MODEL.md) | What are we defending against? |
| [OPERATIONS_RUNBOOK.md](./OPERATIONS_RUNBOOK.md) | How is it started, backed up, restored? |
| [RELEASE_CHECKLIST.md](./RELEASE_CHECKLIST.md) | What gates a release? |
| [EVALUATION_PLAN.md](./EVALUATION_PLAN.md) | How is a model qualified? |

## Stakeholder-facing (Turkish)

| Document | Answers |
|---|---|
| [DEMO_SCRIPT.md](./DEMO_SCRIPT.md) | The verified click path through the product, what to say, what to avoid. |
| [TOOLS_STRATEGY.md](./TOOLS_STRATEGY.md) | How are tools added, what does each tier cost, why is messaging gated? |

## Product and commercial framing

| Document | Answers |
|---|---|
| [PROJECT_ARCHITECTURE.md](./PROJECT_ARCHITECTURE.md) | How does the vision map onto the system? |
| [PRODUCT_DEPLOYMENT_PLAN.md](./PRODUCT_DEPLOYMENT_PLAN.md) | How is this sold and deployed? |
| [PRODUCT_ROADMAP_TO_GOAL.md](./PRODUCT_ROADMAP_TO_GOAL.md) | What is the product trajectory? |

## Scoping documents — unbuilt PRD components

Open questions and constraints, not specifications. Read when scoping one of these.

- [design/POLICY_ENGINE.md](./design/POLICY_ENGINE.md)
- [design/CONSENT_LEDGER.md](./design/CONSENT_LEDGER.md)
- [design/GROWTH_CONTEXT_GRAPH.md](./design/GROWTH_CONTEXT_GRAPH.md)
- [design/DESIGN_SYSTEM.md](./design/DESIGN_SYSTEM.md) — UI conventions

## Decisions

[`adr/`](./adr/) holds every durable architectural decision. There is no other place.
[adr/README.md](./adr/README.md) is the index: which ADRs are load-bearing today, which are
change logs, which references are broken, and how to write a new one.

## Historical record — closed

Kept for traceability. Do not read for working context, do not add to them.

- [ARCHITECTURE_ASSESSMENT.md](./ARCHITECTURE_ASSESSMENT.md) — point-in-time assessment that
  produced the current roadmap. Useful once for depth; the roadmap is the living version.
- [AUDIT_FINDINGS.md](./AUDIT_FINDINGS.md), [AUDIT_RAPORT.md](./AUDIT_RAPORT.md) — earlier
  audit rounds, superseded by the two documents above.
- [archive/](./archive/) — deprecated plans.

---

## Adding a document

Check [AI_DEVELOPMENT_GUIDE.md](./AI_DEVELOPMENT_GUIDE.md) §7 first: most new knowledge
belongs in a document that already exists. A new file is justified when it answers a question
none of the above answers. If you add one, add a row here and say which task types need it in
the guide's reading map — a document nobody is told to read is a document nobody reads.
