# Implementation Status

Last verified: 14 July 2026

This document is the authoritative statement of what the repository actually does. The source PRD
and manager architecture are unchanged vision inputs; they are not completion claims.

## Implemented and verified

### Platform and trust boundary

- [x] Nginx exposes the built React application and FastAPI at `http://localhost:8080`; only the
  ingress proxy publishes a host port.
- [x] Explicit Alembic migrations upgrade empty and known scaffold databases through revision
  `20260713_0007`; application startup does not call `create_all()`.
- [x] Bootstrap, login, logout, current session, users, roles, Argon2 password hashing, session
  cookies, CSRF, role checks, request IDs, structured errors, and security audit records exist.
- [x] Standard Compose disables demo authentication. The named development overlay is the only
  bypass, and production rejects demo auth and weak/default application secrets.
- [x] Production bootstrap/session/master secrets and cloud provider keys can be mounted from
  ignored host files via Docker secrets.
- [x] Health checks query PostgreSQL and report Ollama, qmd, and OKF separately.

### Ingestion, evidence, and knowledge

- [x] Demo and bounded CSV/XLSX sources use read-only connector contracts, schema discovery,
  preview, versioned mappings, classification, sync history, and immutable raw snapshots.
- [x] The Anka fixture produces 1,783 canonical entities and evidence items through the same
  connector pipeline used by uploaded files.
- [x] Citations resolve to the exact immutable snapshot plus sheet/row/column or content locator and
  verified hash.
- [x] OKF 0.1 parse/write, tolerant unknown metadata/type round-trip, validation, links/backlinks,
  index/log, safe ZIP import/export, and lexical search fallback exist.
- [x] Each diagnostic creates an isolated Git candidate. Only serialized approval may fast-forward
  active `main`; rejection/expiry leaves active knowledge unchanged, and qmd reindex is requested
  only after approval.

### Agents, diagnostic, and workflows

- [x] Four typed Pydantic AI agent v2 definitions use explicit Ollama/Groq/Mistral profiles.
  Built-in workflows prefetch bounded inputs through the code-defined capability layer instead of
  permitting free tool loops. Local-to-cloud fallback is prohibited.
- [x] Metrics and opportunity scores are deterministic and derived from persisted data. The six
  planted opportunity/data-quality signals are versioned in the Anka fixture.
- [x] Every material or numerical claim must pass Evidence Reviewer checks against persisted
  evidence before a report/candidate is created.
- [x] Runs persist workflow/agent/model versions, step input hashes, safe errors, provider/model,
  classification/redaction outcome, usage, evidence, and Markdown/HTML/OKF artifacts.
- [x] Agent, Capability, and Workflow drafts/immutable versions; clone/save/validate/dry-run/publish/
  run APIs; safe conditions; typed branches; idempotency; schedules; and histories exist. Draft
  dry-run is explicitly a deterministic simulation and never claims that an agent/model executed.
- [x] Standard Compose starts real DBOS workflows. The PostgreSQL checkpoint runtime is invoked by
  retryable DBOS steps; approvals wait through durable `recv`, and decisions/expiry resume safely.
- [x] The live missing-model drill created the same run ID in DBOS, persisted completed steps, then
  failed at the model node without fallback.

### Product journey

- [x] Setup progress is persisted across all ten steps. Model probe, demo sync, OKF validation,
  diagnostic, report review, and candidate decision call real APIs.
- [x] Sources, Opportunities, Approval Center, Settings/Registry, Dashboard, Knowledge Explorer,
  run trace, and React Flow editor use persisted backend resources.
- [x] Workflow Save, Validate, Dry-run, Publish, and Run are API-connected.
- [x] Turkish-first UI has an i18n boundary, responsive styles, actionable empty/error states, and
  keyboard-native controls for critical forms and buttons.

### Security and operations

- [x] Source instructions remain untrusted data; cloud contact identifiers are redacted and
  confidential/restricted evidence is denied to cloud tools.
- [x] Archive traversal/symlink/bomb, formula-like cells, HTML XSS, auth/CSRF, arbitrary condition
  code, duplicate runs/decisions, and candidate rejection are covered by automated tests.
- [x] Default Docker networking blocks app egress; cloud access requires the allowlisted Squid
  profile for Groq or Mistral.
- [x] Opt-in OpenTelemetry exports content-safe HTTP metrics/traces to digest-pinned Jaeger v2.19.
  The live Jaeger service list contains `agi-control-plane`.
- [x] PowerShell and Linux backup/restore scripts cover the application DB, DBOS system DB, and the
  complete knowledge Git volume with SHA-256 verification and archive path checks.
- [x] A live backup/restore drill restored revision `20260713_0007`, 1,783 entities, DBOS state, and
  healthy service startup.
- [x] Runtime/base images and qmd dependency are digest/version pinned. CycloneDX SBOM generation
  indexed 812 packages; digest-pinned Trivy found zero fixable HIGH/CRITICAL or image-secret
  findings.
- [x] The live qmd profile reindexed the active OKF bundle and returned exact Markdown search
  locators. Stopping qmd kept the application healthy with lexical fallback active.
- [x] An isolated production Compose drill created empty volumes, ran all migrations, bootstrapped
  `admin + analyst + approver`, recorded audit, and returned 401 for an unauthenticated resource.

## Release blockers and deliberately incomplete acceptance

- [ ] **Qualified model:** `qwen3.5:9b` is installed and its real PromptedOutput probe passes. The
  first bounded full diagnostic completed Company Analyst, then Growth Opportunity Analyst failed
  closed after an invalid-output retry exhausted its 360-second v2 budget (622 seconds total).
  Therefore 9B is not release-supported; 27B or governed Groq/Mistral must pass the 20-run suite.
- [ ] **Full live happy path:** the typed test-model suite proves the complete diagnostic/evidence/
  approval path, but the browser cannot complete a real model-assisted report until a model profile
  qualifies.
- [ ] **External clean Linux host:** clean Linux/amd64 containers and empty volumes were verified on
  Docker Desktop; a separate Linux x86-64 host release rehearsal remains required.
- [ ] **TLS termination:** production cookies are `Secure`. The production overlay must sit behind
  operator-managed HTTPS; the repository's port 8080 Nginx endpoint is the local/development
  acceptance endpoint and does not terminate TLS.
- [ ] **Real CRM/ERP:** intentionally deferred until a design partner identifies the actual system.

The product is a production-candidate implementation, not a released MVP, until the first three
release blockers above are closed. External write actions remain prohibited.

## Current verification evidence

- Backend suite: 45 tests; Ruff passes.
- Frontend suite: 6 tests; production build passes.
- Ruff and Alembic drift: pass; migration head `20260713_0007`.
- Compose: base, development, production, cloud, observability, and temporary model-download
  configurations validate.
- Browser smoke: Workflow editor, Approval Center, Settings/Registry, persisted run history, and
  current model-readiness state render at `localhost:8080`.
- Observability smoke: Jaeger v2 UI/API is reachable only in the explicit profile and receives
  `agi-control-plane` OTLP traces; the standard stack was restored afterward.
- No-egress: an HTTPS request from the default app container is blocked.
- Backup/restore and clean-production evidence are recorded above; generated release reports remain
  ignored under `artifacts/release/`.

Run the same repository checks with:

```powershell
.\scripts\project-check.ps1 -Live
```

```bash
./scripts/project-check.sh --live
```

Run profile qualification inside the isolated app network:

```powershell
.\scripts\qualify-model.ps1 -Profile local-balanced -Attempts 20
```

## Active phase

Release qualification: configure one approved model, pass the golden evaluation, run the complete
browser journey, then rehearse the same candidate on a clean Linux x86-64 host.
