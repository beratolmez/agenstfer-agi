# Domain Contracts

This document defines ownership and stable vocabulary for MVP v0.1. Pydantic schemas, SQLAlchemy models, OpenAPI, and UI types must use the same meanings.

## Classification

`DataClassification` is one of `public`, `internal`, `confidential`, or `restricted`.

- Local processing may handle every class subject to role and logging policy.
- Cloud processing may handle `public` and policy-approved, redacted `internal` content.
- Cloud processing must reject `confidential` and `restricted` content.

## Source and evidence

- **DataSource:** configured read-only origin and connector type.
- **SourceMapping:** versioned mapping from discovered fields to canonical fields.
- **SyncRun:** cursor, status, counts, errors, mapping version, and start/end times.
- **RawSnapshot:** immutable content address, source ID, media type, size, collection time, and storage URI.
- **EvidenceItem:** source/snapshot ID, exact locator, excerpt hash, classification, and collection time.

A tabular locator contains sheet/table, row, and column. A text locator contains section and line range when available plus content hash. Evidence never points only to a mutable external URL.

## Context and knowledge

- **CanonicalEntity:** source-neutral business entity with external keys and classified attributes.
- **CanonicalFact:** typed relation or value with evidence IDs and optional validity time.
- **OKF Concept:** portable Markdown/YAML knowledge. Unknown types and frontmatter survive round-trip.
- **OKF Candidate:** isolated proposed revision associated with one workflow run.
- **OKF Active Revision:** approved Git `main` revision used for retrieval.

PostgreSQL owns operational state and evidence locators. OKF owns portable company knowledge. qmd owns neither.

## Agents, workflows, and artifacts

- **Capability:** code-defined, versioned, allowlisted tool contract.
- **Agent Version:** immutable published prompt, output schema, capability versions, default model profile, and policy limits.
- **Workflow Draft:** editable typed DAG.
- **Workflow Version:** immutable published DAG referencing exact agent and capability versions.
- **Workflow Run:** idempotent execution pinned to workflow and model profiles.
- **Step Run:** attempt, timing, status, safe input/output references, provider/model profile,
  classification/redaction outcome, usage, and safe error metadata.
- **Approval Request:** pending decision, requested role, artifact, expiry, actor, reason, and decision time.
- **Artifact:** content-addressed diagnostic, report, trace, or OKF candidate produced by a run.

Published objects are immutable. A new edit creates a new version.

## Typed diagnostic outputs

- `CompanyAnalysis`: profile, segments, strengths, weaknesses, data gaps, and evidence IDs.
- `OpportunityHypotheses`: exactly the five allowlisted deterministic opportunity signals, with
  evidence IDs and metric inputs.
- `EvidenceReview`: claim-level supported/rejected/stale/contradictory decisions.
- `GrowthDiagnostic`: company summary, readiness, top five scored opportunities, evidence coverage, gaps, and 30-day plan.

The recommendation score is deterministic prioritization, not probability or model confidence.
