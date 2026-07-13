# ADR-0007: Approval-controlled OKF candidate lifecycle

## Status

Accepted — 13 July 2026

## Decision

The active company bundle is the approved Git `main` revision. Each diagnostic run writes an isolated candidate revision associated with the run and artifact hashes. Validation and evidence review happen before approval. An authenticated Approver may merge one non-stale candidate at a time. Rejected, expired, or conflicting candidates never alter active knowledge.

qmd indexes only the active revision and is refreshed after a successful merge. PostgreSQL stores candidate/run/approval state; Git stores portable knowledge history.

## Consequences

Candidate generation is safe to retry and approval is auditable. Merge serialization is required for the single-company MVP. The application must surface stale-base conflicts rather than overwriting newer approved knowledge.

