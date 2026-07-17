# ADR-0010: Langfuse observability boundary

## Status

Accepted — 17 July 2026

## Context

The product needs model, agent, workflow, and evaluation visibility for vendor support and customer
operations. The data may contain company-sensitive evidence, so a hosted observability service must
not receive raw prompts or source content by default. OpenTelemetry and Jaeger already provide a
content-safe baseline.

## Decision

OpenTelemetry remains the application instrumentation interface. Langfuse is an optional,
self-hosted, customer-isolated trace and evaluation sink. Jaeger remains the minimal local fallback.
The Langfuse integration records only content-safe metadata: provider/model, versions, duration,
token totals, retry counts, validation outcomes, evidence counts, classifications, and safe hashes.

Prompt bodies, source bodies, evidence excerpts, secrets, and contact identifiers are excluded by
default. Any hosted or centralized Langfuse use requires explicit customer approval, classification
and redaction checks, retention rules, access control, and an updated egress policy. Self-hosted
telemetry/licensing behavior must be verified during release qualification.

## Consequences

- Model failures and drift can be investigated without making Langfuse the source of truth.
- Each customer can retain traces inside its own private environment.
- Langfuse deployment, storage, backup, upgrade, and access control become operational work.
- Prompt management or raw trace capture cannot be enabled as an undocumented debugging shortcut.

