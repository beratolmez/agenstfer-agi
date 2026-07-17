# ADR-0009: Productized isolated customer deployments

## Status

Accepted — 17 July 2026

## Context

The product is prepared and sold by the vendor, with ongoing updates and support. Customer data
security rules out assuming a shared SaaS database. The manager target architecture includes AWS,
container clusters, business modules, and a local GPU option, while the current MVP is a single-host
Compose deployment.

## Decision

The product is delivered as one isolated installation per customer company. The first production
deployment may be a customer-isolated AWS VPC, but AWS account ownership, runtime selection, TLS,
backup, update, rollback, and support telemetry must be explicit deployment decisions. Shared SaaS
multi-tenancy is out of scope until a new ADR changes the boundary.

The application keeps one provider-neutral control-plane contract across local, managed AWS,
customer AWS, and later split-private profiles. PostgreSQL and the OKF/Git boundary does not change
between profiles. Vendor-delivered images and migrations are versioned and signed; customer updates
are backup-first and reversible.

## Consequences

- Customer data, knowledge history, model secrets, and observability data are isolated.
- The vendor must maintain release, migration, rollback, compatibility, and support procedures.
- AWS infrastructure and local-GPU networking are part of deployment engineering, not hidden inside
  agent code.
- A future shared control plane would require a new threat model, tenancy model, data-isolation
  design, and ADR.

## Alternatives rejected

- Shared SaaS tenancy for the MVP: conflicts with the security and single-company boundary.
- A mandatory single AWS topology: would prevent customer-private and local deployments.
- Customer-supplied arbitrary plugins: would bypass the product capability and update boundary.

