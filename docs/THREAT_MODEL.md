# MVP Threat Model

## Protected assets

Company source content, credentials, personal/contact data, canonical context, OKF history, prompts, model configuration, workflow/approval state, audit integrity, and backups.

## Trust boundaries

1. Browser to Nginx/FastAPI.
2. FastAPI to PostgreSQL, raw vault, Git bundle, Ollama, and qmd.
3. Optional FastAPI to allowlisted cloud providers through the egress gateway.
4. Uploaded files and document text entering trusted processing as untrusted data.

## Mandatory controls

- Session authentication, CSRF, role enforcement, production Secure cookies behind HTTPS,
  bootstrap closure, and audit.
- Internal Docker network; only ingress proxy publishes a host port.
- Explicit model installation grants temporary outbound access only to Ollama and restores its
  internal-only network even after pull failure.
- Connector and agent capability allowlists; no arbitrary code or unrestricted URL tools.
- Immutable snapshots, path confinement, archive cumulative-size limits, and symlink rejection.
- Aggregate metric receipts are content-addressed and bind every member evidence ID/snapshot/excerpt/classification
  hash. Resolution must reject a changed receipt, missing member, nested derived member, or digest
  mismatch before the value reaches Evidence Reviewer. A numerical claim without a receipt must not
  fall back to representative raw rows; unknown evidence classifications block receipt creation.
- HTML export escaping. Formula-like imported cells are flagged as untrusted; any future CSV export
  must escape formula prefixes.
- Prompt-injection separation: source content cannot modify system policy or tool scope.
- Classification and redaction before cloud calls; block confidential/restricted data.
- Installation configuration accepts only code-defined model profiles, source modes, locales, and
  bounded company fields. A UI-provided provider URL, model identifier, or secret is never trusted.
- Compose allowlists application environment variables. Cloud API keys are mounted only as the
  cloud-profile secret file and are never inherited by PostgreSQL or the base app environment.
- Do not log secrets, prompts, source bodies, or evidence excerpts.
- Release evidence must reject content-bearing secret/prompt/source fields, independently validate
  model/restart claims, and hash-bind required artifacts before a rehearsal can report success.
- Idempotent workflows and approvals; stale/replayed decisions fail closed.
- Cancellation changes application/approval/candidate state only after DBOS confirms cancellation;
  retry cannot substitute a newer workflow for the run's pinned immutable version.
- Approval-controlled OKF merge and conflict detection.

## Required negative tests

Authentication bypass, missing/wrong role, CSRF, session fixation, prompt injection, stored/reflected
XSS, formula-like spreadsheet cells, path traversal, archive bomb/symlink, secret/log leakage,
unexpected egress, duplicate run/approval, stale candidate, and restore tampering. SSRF/private IP/DNS
rebinding/redirect tests become mandatory before adding a URL connector; no URL capability exists in
the MVP build.
Metric-receipt tampering and missing-member rejection are mandatory for numerical-claim changes.

## Deferred risks

TLS certificate lifecycle/termination is owned by the deployment operator. Real CRM/ERP OAuth,
website crawling, OCR, SSO, external write actions, messaging, voice, and multi-tenant isolation are
outside MVP. Each requires a new threat-model section and ADR before implementation.
