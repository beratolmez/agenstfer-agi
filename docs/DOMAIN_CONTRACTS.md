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
- **Deterministic Metric Receipt:** a derived EvidenceItem for an aggregate numerical claim. It
  contains the calculation version, exact metric/factor/score output, member count, and a digest over
  every member EvidenceItem ID, snapshot hash, excerpt hash, and classification. Its locator retains the complete
  member ID list so resolution can revalidate the chain to immutable raw snapshots.

A tabular locator contains sheet/table, row, and column. A text locator contains section and line range when available plus content hash. Evidence never points only to a mutable external URL.
An aggregate receipt never replaces its raw members and is not model-authored evidence; a few
representative rows are insufficient proof of an aggregate value.

## Context and knowledge

- **CanonicalEntity:** source-neutral business entity with external keys and classified attributes.
- **CanonicalFact:** typed relation or value with evidence IDs and optional validity time.
- **OKF Concept:** portable Markdown/YAML knowledge. Unknown types and frontmatter survive round-trip.
- **OKF Candidate:** isolated proposed revision associated with one workflow run.
- **OKF Active Revision:** approved Git `main` revision used for retrieval.

PostgreSQL owns operational state and evidence locators. OKF owns portable company knowledge. qmd owns neither.

## Agents, workflows, and artifacts

- **Capability:** code-defined, versioned, allowlisted tool contract.
- **Agent Draft:** administrator-editable typed definition with a code-allowlisted model profile,
  output type, capabilities, classification, risk, timeout, token budget, and versioned instruction.
- **Agent Version:** immutable published typed definition. The versioned instruction is composed with
  an immutable control-plane system policy at execution time; it is never the complete trust policy.
- **Workflow Draft:** editable typed DAG.
- **Workflow Version:** immutable published DAG whose agent nodes contain exact `agent_id` +
  `agent_version` bindings and code-defined capability contracts.
- **Workflow Run:** idempotent execution pinned to workflow and model profiles.
- **Step Run:** attempt, timing, status, safe input/output references, provider/model profile,
  classification/redaction outcome, usage, and safe error metadata.
- **Approval Request:** pending decision, requested role, artifact, expiry, actor, reason, and decision time.
- **Artifact:** content-addressed diagnostic, report, trace, or OKF candidate produced by a run.

Published objects are immutable. A new edit creates a new version through the clone operation. A new
agent ID must start at version 1; clients cannot forge a later version by PUT. Full prompt detail is
admin-only. Workflow publication must resolve each agent reference and reject output-type or model-
profile mismatches. Capability IDs remain code-defined and allowlisted.

A **Workflow Schedule** references one published workflow version and stores a validated cron,
timezone, enabled state, next-run time, and duplicate-run guard. Enabling or disabling it is an
authenticated admin operation and is audited.

The v0.1 `POST /api/diagnostics/run` compatibility contract accepts only a published workflow ID and
version and returns a persisted run descriptor. Clients obtain the diagnostic from run state; this
view cannot accept an inline definition or execute the legacy synchronous service. Model-profile
discovery returns code-defined identifiers and configuration/availability metadata, never provider
keys. A run's top-level profile is derived from its published agent nodes; each step retains the exact
resolved provider and model.

## Commercial deployment contracts

- **DeploymentProfile:** `local_private`, `managed_aws_private`, `customer_aws_private`, or
  `split_private`. It records the control-plane owner, inference pattern, TLS boundary, backup
  owner, update channel, and observability policy.
- **InferenceNetworkPattern:** `same_private_vpc`, `site_to_site_vpn`, or
  `outbound_inference_gateway`. Public Ollama/vLLM endpoints are invalid.
- **ObservabilityEvent:** content-safe provider/model, agent/workflow versions, timing, token totals,
  retry/validation outcome, classification, evidence counts, and safe hashes. Prompt/source/evidence
  bodies and secrets are not valid fields.
- **ProductRelease:** signed image/package set, migration range, SBOM/vulnerability evidence,
  compatibility, rollback version, and release notes.

## Bounded task orchestration contracts

- **TaskPlan:** a typed user goal, bounded worker tasks, dependencies, capability scopes,
  classification, maximum rounds, maximum workers, timeout, token/cost budget, and completion criteria.
- **WorkerTask:** a code-defined worker profile plus immutable input/evidence references and a typed
  output contract. It cannot contain executable code or an arbitrary provider/tool URL.
- **RoundOutcome:** one of `complete`, `continue`, `blocked`, `needs_human_approval`, or
  `budget_exceeded`, with unresolved task IDs and evidence references.

These contracts are post-MVP. They must be persisted through DBOS and evaluated separately before a
dynamic worker workflow can be enabled for customer installations.

## Typed diagnostic outputs

- `CompanyAnalysis`: profile, segments, strengths, weaknesses, data gaps, and evidence IDs.
- `OpportunityHypotheses`: exactly the five allowlisted deterministic opportunity signals, with
  evidence IDs and metric inputs.
- `EvidenceReview`: claim-level supported/rejected/stale/contradictory decisions.
- `GrowthDiagnostic`: company summary, readiness, top five scored opportunities, evidence coverage, gaps, and 30-day plan.

The recommendation score is deterministic prioritization, not probability or model confidence.
