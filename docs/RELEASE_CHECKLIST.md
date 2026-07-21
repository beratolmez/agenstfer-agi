# MVP Release Checklist

Last audited: 17 July 2026

The release is a customer-isolated product release, not a shared SaaS release. The first AWS
runtime, customer account/VPC ownership, inference network, update/rollback path, and observability
profile must be recorded before a production claim.

## Build and migration

- [x] Empty-volume Linux containers start and migrate through `20260713_0007`.
- [x] Backend tests/lint (FastAPI), frontend tests/build (React), Alembic drift, and Compose validation pass.
- [x] Base, development, production, cloud, and observability configurations validate.
- [x] Runtime/base images and ChromaDB dependencies are pinned.
- [x] Local ChromaDB reindex/search and loss-to-lexical-fallback drill passes.
- [ ] Repeat on a separate clean Linux x86-64 host behind HTTPS.

## Functional journey

- [x] Bootstrap creates one audited Admin/Analyst/Approver; unauthenticated access returns 401.
- [x] Demo data uses connector, mapping, persistence, immutable snapshot, and evidence pipelines.
- [x] Typed Pydantic AI test models produce evidence-reviewed reports/candidates/artifacts.
- [x] Candidate approval merges and rejection leaves active knowledge unchanged in integration tests.
- [x] Workflow edit/validate/dry-run/publish/run/history and LangGraph missing-model failure path work.
- [x] OKF export/import preserves unknown types and metadata.
- [x] Isolated React browser E2E verifies truthful no-result dashboard state, model-profile discovery,
  persisted setup/demo sync, Sources UI, Agent Registry create/publish, and workflow
  dry-run/publish/version/schedule management.
- [x] The qualification harness exercises a profile-pinned published persistent workflow and binds
  exact agent versions, effective-prompt hashes, and the running code's exact policy revision in
  independently validated content-safe evidence.
- [ ] A real Gemini API model passes structured-output and 20-run golden qualification.
- [ ] The opt-in real-model Browser E2E completes diagnostic, exact citation, durable approval,
  active merge, and export. The executable suite exists; no real provider has passed it yet.
- [ ] Restart during a real agent step and approval resumes the same LangGraph state/run ID.
  The Linux rehearsal now performs and independently validates both interruptions; execution evidence
  from the qualified external host is still required before checking this item.

## Quality and security

- [x] Auth/CSRF, prompt injection, HTML XSS, formula-like source, archive/path/symlink/size,
  classification/redaction, safe conditions, idempotency, and approval rejection tests exist.
- [x] Aggregate metric receipts bind complete raw-evidence membership and reject member/hash/digest
  tampering before numerical claims reach Evidence Reviewer.
- [x] Default deployment has no unexpected app egress.
- [x] Cloud keys and production application secrets use ignored host/Docker secret files.
- [x] OTLP telemetry excludes prompts, source bodies, evidence excerpts, and secrets; a Jaeger v2
  live smoke received the `agi-control-plane` service.
- [x] CycloneDX SBOM exists; digest-pinned Trivy reports zero fixable HIGH/CRITICAL and image-secret
  findings for the audited image.
- [ ] Every release-enabled model profile passes all `EVALUATION_PLAN.md` gates.
- [ ] Run ChromaDB loss/rebuild and final log-leak review on the release host.

## Recovery and handoff

- [x] Checksummed application DB + LangGraph DB + knowledge backup restores and restarts successfully.
- [x] PowerShell and Linux wrappers exist for checks, backup/restore, egress, scan, and secret setup.
- [x] An external Linux x86-64 rehearsal command and fail-closed evidence manifest schema exist;
  it composes qualification, real-model E2E, same-run agent/approval restart, recovery, lexical
  fallback, and ChromaDB rebuild gates. Required evidence artifacts are independently validated and
  SHA-256-bound; the rehearsal itself has not yet passed on the required host.
- [x] Architecture, operations, threat, status, and implementation documents match the candidate.
- [ ] Verify restored diagnostic artifacts/citations after a real successful Gemini API run.
- [ ] Tag/release only after all unchecked release requirements above are closed.

## Commercial deployment readiness

- [ ] Select and document the first AWS runtime and IaC/image/secret contract.
- [ ] Document customer account/VPC ownership, TLS termination, private subnets, and inference
  network pattern; unauthenticated/public API access is prohibited.
- [ ] Package signed images, migrations, SBOM, vulnerability evidence, release notes, and rollback
  instructions.
- [ ] Complete one customer-style backup → update → migration → smoke-test → rollback drill.
- [ ] Add self-hosted Langfuse behind OpenTelemetry or document the Jaeger-only profile. Verify
  content-safe fields, retention, RBAC, backup, licensing, and telemetry settings.
- [ ] Publish starter small-company capacity and diagnostic-concurrency policy.
- [ ] Keep bounded task orchestration disabled until its separate evaluation and recovery gate passes.
