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
- **Deterministic Metric Receipt:** a derived EvidenceItem for an aggregate numerical claim.

## Context and knowledge

- **CanonicalEntity:** source-neutral business entity with external keys and classified attributes.
- **CanonicalFact:** typed relation or value with evidence IDs and optional validity time.
- **OKF Concept:** portable Markdown/YAML knowledge.
- **OKF Candidate:** isolated proposed revision associated with one workflow run.
- **OKF Active Revision:** approved Git `main` revision used for retrieval.

PostgreSQL owns operational state and evidence locators, and is also what workflow runs are resumed from. LangGraph currently compiles with an in-memory checkpointer, so checkpoints do not survive a process restart; ADR-0029 accepted moving to a PostgreSQL checkpointer, which is not yet implemented. Retrieval is one layer with two paths over the same active bundle: the OKF Wiki is the source of truth and the vector index is a derived, disposable projection of it (ADR-0031).

## Agents, workflows, and artifacts

- **Capability:** code-defined, versioned, allowlisted tool contract.
- **Agent Draft:** administrator-editable typed definition.
- **Agent Version:** immutable published typed definition.
- **Workflow Draft:** editable typed DAG using LangGraph nodes.
- **Workflow Version:** immutable published LangGraph DAG.
- **Workflow Run:** idempotent execution pinned to workflow and model profiles, managed via FastAPI.
- **Step Run:** LangGraph node transition step.
- **Approval Request:** the run is persisted as `awaiting_approval` and resumed from the database on decision. LangGraph `interrupt_before`/`interrupt_after` is accepted as the target but not yet used (ADR-0029).
- **Artifact:** content-addressed diagnostic, report, trace, or OKF candidate produced by a run.

## Commercial deployment contracts

- **DeploymentProfile:** `local_private`, `managed_aws_private`, `customer_aws_private`, or `split_private`.
- **InferenceNetworkPattern:** `same_private_vpc`, `site_to_site_vpn`, or `outbound_inference_gateway`.
- **ObservabilityEvent:** content-safe provider/model, agent/workflow versions, timing, token totals.
- **ProductRelease:** signed image/package set, migration range.

## Typed diagnostic outputs

- `CompanyAnalysis`: profile, segments, strengths, weaknesses, data gaps, and evidence IDs.
- `OpportunityHypotheses`: exactly the five allowlisted deterministic opportunity signals, with evidence IDs and metric inputs.
- `EvidenceReview`: claim-level supported/rejected/stale/contradictory decisions.
- `GrowthDiagnostic`: company summary, readiness, top five scored opportunities, evidence coverage, gaps, and 30-day plan.

The recommendation score is deterministic prioritization, not probability or model confidence.
