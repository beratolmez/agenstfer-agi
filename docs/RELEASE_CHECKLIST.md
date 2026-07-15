# MVP Release Checklist

Last audited: 15 July 2026

## Build and migration

- [x] Empty-volume Linux containers start and migrate through `20260713_0007`.
- [x] Backend tests/lint, frontend tests/build, Alembic drift, and Compose validation pass.
- [x] Base, development, production, cloud, and observability configurations validate.
- [x] Runtime/base images and qmd dependency are pinned.
- [x] Local qmd reindex/search and loss-to-lexical-fallback drill passes.
- [ ] Repeat on a separate clean Linux x86-64 host behind HTTPS.

## Functional journey

- [x] Bootstrap creates one audited Admin/Analyst/Approver; unauthenticated access returns 401.
- [x] Demo data uses connector, mapping, persistence, immutable snapshot, and evidence pipelines.
- [x] Typed Pydantic AI test models produce evidence-reviewed reports/candidates/artifacts.
- [x] Candidate approval merges and rejection leaves active knowledge unchanged in integration tests.
- [x] Workflow edit/validate/dry-run/publish/run/history and DBOS missing-model failure path work.
- [x] OKF export/import preserves unknown types and metadata.
- [x] Isolated browser E2E verifies truthful no-result dashboard state, persisted setup/demo sync,
  Sources UI, and workflow clone plus explicitly labeled deterministic dry-run.
- [ ] A real release model passes structured-output and 20-run golden qualification.
- [ ] Browser E2E completes diagnostic, exact citation, durable approval, active merge, and export.
- [ ] Restart during a real agent step and approval resumes the same DBOS/run ID.

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
- [ ] Every release-enabled model passes all `EVALUATION_PLAN.md` gates.
- [ ] Run qmd loss/rebuild and final log-leak review on the release host.

## Recovery and handoff

- [x] Checksummed application DB + DBOS DB + knowledge backup restores and restarts successfully.
- [x] PowerShell and Linux wrappers exist for checks, backup/restore, egress, scan, and secret setup.
- [x] Architecture, operations, threat, status, and implementation documents match the candidate.
- [ ] Verify restored diagnostic artifacts/citations after a real successful model run.
- [ ] Tag/release only after all unchecked release requirements above are closed.
