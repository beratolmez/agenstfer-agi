# MVP Threat Model

## Protected assets

Company source content, credentials, personal/contact data, canonical context, OKF history, prompts, model configuration, workflow/approval state, audit integrity, and backups.

## Trust boundaries

1. Browser to Nginx/FastAPI.
2. FastAPI to PostgreSQL, raw vault, Git bundle, Ollama, and qmd.
3. Optional FastAPI to allowlisted cloud providers through the egress gateway.
4. Uploaded files and document text entering trusted processing as untrusted data.

## Mandatory controls

- Session authentication, CSRF, role enforcement, secure cookies, bootstrap closure, and audit.
- Internal Docker network; only ingress proxy publishes a host port.
- Connector and agent capability allowlists; no arbitrary code or unrestricted URL tools.
- Immutable snapshots, path confinement, archive cumulative-size limits, and symlink rejection.
- HTML/Markdown sanitization and CSV formula escaping.
- Prompt-injection separation: source content cannot modify system policy or tool scope.
- Classification and redaction before cloud calls; block confidential/restricted data.
- Do not log secrets, prompts, source bodies, or evidence excerpts.
- Idempotent workflows and approvals; stale/replayed decisions fail closed.
- Approval-controlled OKF merge and conflict detection.

## Required negative tests

Authentication bypass, missing/wrong role, CSRF, session fixation, prompt injection, stored/reflected XSS, SSRF/private IP/DNS rebinding, redirect escape, CSV formula injection, path traversal, archive bomb, archive symlink, malicious spreadsheet, secret/log leakage, unexpected egress, duplicate run, duplicate approval, stale candidate, and restore tampering.

## Deferred risks

Real CRM/ERP OAuth, website crawling, OCR, SSO, external write actions, messaging, voice, and multi-tenant isolation are outside MVP. Each requires a new threat-model section and ADR before implementation.

