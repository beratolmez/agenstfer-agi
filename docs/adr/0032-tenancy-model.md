# ADR-0032: Tenancy Model — Resolving the PRD / AGENTS.md Contradiction

- **Status:** Proposed — decision required
- **Date:** 28 July 2026
- **Blocks:** the data-boundary architecture; gates ADR-0030 option B
- **Relates to:** ADR-0009 (productized isolated customer deployments)

## Context

The product's two governing documents require opposite things, and no ADR records the
conflict.

- **PRD §9** lists `Multi tenant isolation` and `Tenant level data boundary` as security
  requirements.
- **AGENTS.md** states: *"One customer installation serves one company … do not introduce
  shared SaaS multi-tenancy without a new ADR."*

The code follows AGENTS.md. There is no tenant concept anywhere — `rg -i "tenant"` over
`apps/` returns nothing. Single-company assumptions are structural, not incidental:

- `InstallationState` is a single row keyed `"default"` (`main.py:641`)
- The OKF active bundle is one Git repository at one path (`config.py:86-89`)
- Evidence, canonical entities and runs carry no tenant discriminator
- The knowledge volume is one mount for the whole deployment

So today the product is single-tenant by construction, and ADR-0009 already chose
"isolated customer deployment" as the commercial model. The contradiction is that the PRD
has never been amended to match, which leaves the security requirements section describing a
system nobody is building.

## Options

**A. Confirm single-tenant; amend the PRD.** Record that isolation is achieved by deployment
separation — one installation, one database, one knowledge volume, one customer — rather than
by row-level tenancy. Update PRD §9 so `Multi tenant isolation` reads as
`Deployment-level tenant isolation`, and state the operational consequences: per-customer
backup/restore, per-customer upgrade, per-customer quota.
*Cost:* documentation only. *Consequence:* per-customer operational overhead scales linearly;
that is already the model ADR-0009 chose.

**B. Introduce row-level multi-tenancy.** Add a tenant discriminator to every operational
table, scope every query, partition the knowledge volume and the OKF Git repositories, and
extend the threat model to cover cross-tenant leakage through the shared model gateway and
the shared retrieval index.
*Cost:* very high, and it touches every table, every query and the evidence chain. It also
introduces a class of vulnerability the product currently cannot have.
*Consequence:* one deployment serves many customers; operational cost per customer drops.

## Recommendation

**A.** The code, ADR-0009 and the deployment tooling are already aligned on deployment-level
isolation, and it is the stronger security posture for a product whose core promise is
evidence custody: a tenant-scoped query bug in option B would be a cross-customer evidence
leak, which is precisely the failure this product cannot afford.

If B is ever required commercially, it should be a deliberate re-platforming with its own
threat model — not an incremental change layered onto the current schema.

## Consequences of not deciding

Every downstream boundary decision inherits the ambiguity. ADR-0030 option B (a live MCP
egress path) cannot be scoped without knowing whether one process may hold more than one
customer's data, and neither can the model-tiering and quota work in ADR-0033.
