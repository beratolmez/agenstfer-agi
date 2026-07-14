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
- HTML export escaping. Formula-like imported cells are flagged as untrusted; any future CSV export
  must escape formula prefixes.
- Prompt-injection separation: source content cannot modify system policy or tool scope.
- Classification and redaction before cloud calls; block confidential/restricted data.
- Do not log secrets, prompts, source bodies, or evidence excerpts.
- Idempotent workflows and approvals; stale/replayed decisions fail closed.
- Approval-controlled OKF merge and conflict detection.

## Required negative tests

Authentication bypass, missing/wrong role, CSRF, session fixation, prompt injection, stored/reflected
XSS, formula-like spreadsheet cells, path traversal, archive bomb/symlink, secret/log leakage,
unexpected egress, duplicate run/approval, stale candidate, and restore tampering. SSRF/private IP/DNS
rebinding/redirect tests become mandatory before adding a URL connector; no URL capability exists in
the MVP build.

## Deferred risks

TLS certificate lifecycle/termination is owned by the deployment operator. Real CRM/ERP OAuth,
website crawling, OCR, SSO, external write actions, messaging, voice, and multi-tenant isolation are
outside MVP. Each requires a new threat-model section and ADR before implementation.
