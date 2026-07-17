# Implementation Status

Last verified: 17 July 2026

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
- [x] Compose allowlists app/PostgreSQL environment values instead of importing `.env` wholesale;
  cloud API keys enter containers only through the opt-in cloud secret mount.
- [x] Health checks query PostgreSQL and report Ollama, qmd, and OKF separately.

### Ingestion, evidence, and knowledge

- [x] Demo and bounded CSV/XLSX sources use read-only connector contracts, schema discovery,
  preview, versioned mappings, classification, sync history, and immutable raw snapshots.
- [x] The Anka fixture produces 1,783 canonical entities and evidence items through the same
  connector pipeline used by uploaded files.
- [x] Citations resolve to the exact immutable snapshot plus sheet/row/column or content locator and
  verified hash.
- [x] Aggregate numerical claims use persisted deterministic metric receipts rather than treating a
  few representative rows as proof. Each receipt binds calculation version, values, factor/score,
  source count, and the complete raw-evidence membership digest; resolution revalidates the chain.
  A missing receipt (including legacy in-flight state) fails closed instead of falling back to rows.
- [x] OKF 0.1 parse/write, tolerant unknown metadata/type round-trip, validation, links/backlinks,
  index/log, safe ZIP import/export, and lexical search fallback exist.
- [x] Each diagnostic creates an isolated Git candidate. Only serialized approval may fast-forward
  active `main`; rejection/expiry leaves active knowledge unchanged, and qmd reindex is requested
  only after approval.

### Agents, diagnostic, and workflows

- [x] Four typed, versioned Pydantic AI agent definitions use explicit Ollama/Groq/Mistral profiles.
  Company Analyst v3 bounds summary/claim cardinality and output; Growth Opportunity Analyst v3
  requires exactly the five deterministic signals; Evidence Reviewer v3 processes deterministic
  claim/evidence batches and rejects incomplete or duplicate decision sets. Prior published versions
  remain identifiable in persisted run history.
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
- [x] Agent contracts are server-bounded and version lineage is clone-only. Editable agent
  instructions are composed with an immutable untrusted-data/tool/evidence policy. Workflow publish
  rejects unresolved agents, output-contract mismatches, unknown model profiles, and missing required
  diagnostic roles.
- [x] Standard Compose starts real DBOS workflows. The PostgreSQL checkpoint runtime is invoked by
  retryable DBOS steps; approvals wait through durable `recv`, and decisions/expiry resume safely.
- [x] Published Growth Diagnostic workflow v3 pins and runs exact versions of all four typed agents,
  including Wiki Curator,
  before report creation and durable approval. Its persisted output is the Dashboard data source.
- [x] The deprecated `POST /api/diagnostics/run` compatibility view now starts only an immutable
  published workflow through the DBOS runtime. Setup and Dashboard no longer invoke the old synchronous
  service path. Each run's top-level model profile is derived from its published agent nodes rather than
  being mislabeled with the installation default.
- [x] The live missing-model drill created the same run ID in DBOS, persisted completed steps, then
  failed at the model node without fallback.

### Product journey

- [x] Setup progress is persisted across all ten steps. Model probe, demo sync, OKF validation,
  diagnostic, report review, and candidate decision call real APIs.
- [x] Setup discovers the code-defined local/cloud profile catalog, prevents selection of a disabled
  cloud profile, probes the selected profile, and creates or reuses an immutable workflow version with
  that profile pinned before starting and polling the diagnostic run.
- [x] Sources, Opportunities, Approval Center, Settings/Registry, Dashboard, Knowledge Explorer,
  run trace, and React Flow editor use persisted backend resources.
- [x] Dashboard has no synthetic diagnostic fallback. Before a successful evidence-reviewed run it
  shows a truthful empty state and offers only the real diagnostic action.
- [x] Agent Registry create/clone/edit/save/publish/version detail and Workflow Save, Validate,
  Dry-run, Publish, Run, version-history, schedule-create, and schedule-toggle are API-connected.
- [x] Turkish-first UI has an i18n boundary, responsive styles, actionable empty/error states, and
  keyboard-native controls for critical forms and buttons.

### Security and operations

- [x] Source instructions remain untrusted data. Cloud contact identifiers are redacted at the
  final model boundary; diagnostic steps inherit the highest classification across their complete
  persisted canonical/evidence scope, and any confidential/restricted member blocks cloud execution before
  prompt transmission.
- [x] Installation model/source/locale/company fields are allowlist and bounds validated. Durable run
  cancellation fails closed: DBOS cancellation must succeed before run, approval, or candidate state
  can be changed. Retry always uses the exact pinned published workflow version, including built-ins.
- [x] Archive traversal/symlink/bomb, formula-like cells, HTML XSS, auth/CSRF, arbitrary condition
  code, duplicate runs/decisions, and candidate rejection are covered by automated tests.
- [x] Default Docker networking blocks app egress; cloud access requires the allowlisted Squid
  profile and HTTPS CONNECT to Groq or Mistral on port 443.
- [x] Opt-in OpenTelemetry exports content-safe HTTP metrics/traces to digest-pinned Jaeger v2.19.
  The live Jaeger service list contains `agi-control-plane`.
- [x] PowerShell and Linux backup/restore scripts cover the application DB, DBOS system DB, and the
  complete knowledge Git volume with SHA-256 verification and archive path checks.
- [x] Backup/restore restarts the original app container rather than recreating it from a possibly
  different Compose overlay, preserving production/cloud security configuration.
- [x] A live backup/restore drill restored revision `20260713_0007`, 1,783 entities, DBOS state, and
  healthy service startup.
- [x] The overlay-preservation regression drill kept the exact same app container ID through both
  backup and restore, then returned a healthy API; recovery did not recreate the app from base Compose.
- [x] Runtime/base images and qmd dependency are digest/version pinned. CycloneDX SBOM generation
  indexed 812 packages; digest-pinned Trivy found zero fixable HIGH/CRITICAL or image-secret
  findings.
- [x] The live qmd profile reindexed the active OKF bundle and returned exact Markdown search
  locators. Stopping qmd kept the application healthy with lexical fallback active.
- [x] An isolated production Compose drill created empty volumes, ran all migrations, bootstrapped
  `admin + analyst + approver`, recorded audit, and returned 401 for an unauthenticated resource.
- [x] The external-host rehearsal now coordinates two exact-container interruptions against one real
  DBOS run: one while an agent step is `running` and one while approval is `pending`. Its content-safe
  evidence validator rejects inconsistent qualification attempts, unsupported claims, changed run or
  container IDs, forbidden content fields, missing artifacts, and false-pass manifests. This tooling
  has unit/build/syntax coverage; it is not proof that the external-host restart gate passed.
- [x] Model qualification now clones/publishes the current v3 workflow, pins the requested profile
  and exact agents, and runs the production persistent interpreter. Reports bind workflow, agent,
  policy revision, and effective-prompt hashes; the independent validator rejects the legacy
  synchronous path and content-bearing evidence.

## Release blockers and deliberately incomplete acceptance

- [ ] **Qualified model:** `qwen3.5:9b` is installed and its real structured-output probe passes.
  Company Analyst v3 passed an isolated real call in 171.5 seconds; Growth Opportunity Analyst v3
  produced all five signal IDs in 278.29 seconds; and a five-receipt Evidence Reviewer batch returned
  `5/5 supported` in 165.78 seconds. These component results did not compose into a reliable full
  run. One full attempt failed at Evidence Reviewer after 939.27 seconds with
  `UnexpectedModelBehavior`; the latest telemetry-enabled attempt failed at Company Analyst after
  307.53 seconds when an invalid-output retry exhausted its budget. Native JSON Schema produced
  `json_invalid`; ToolOutput was also rejected after Ollama returned malformed function-call XML with
  HTTP 500. PromptedOutput remains configured and 9B remains development-only. No full successful
  diagnostic or 20-run suite exists; suitable 27B hardware or governed Groq/Mistral is next. The
  ADR-0008 immutable control-plane policy changed the effective prompt, so the historical component
  observations do not qualify the current build. A current production-path smoke pinned workflow
  `qualification-local-balanced:1`, exact agent versions `3/3/3/2`, retrieval and prompt/policy
  provenance, then failed closed at `company_agent` with `TimeoutError` after 313.34 seconds.
- [ ] **Full live happy path:** the typed test-model suite proves the complete diagnostic/evidence/
  approval path, but the browser cannot complete a real model-assisted report until a model profile
  qualifies. An opt-in destructive Playwright suite and wrappers now encode the four-agent DBOS run,
  exact citation, same-run agent/approval restart coordination, approval, active merge, and export
  acceptance; they have not passed a real model.
- [ ] **External clean Linux host:** clean Linux/amd64 containers and empty volumes were verified on
  Docker Desktop; a separate Linux x86-64 host release rehearsal remains required. The new
  `scripts/release-rehearsal.sh` command fails outside Linux x86-64 and records independently
  validated, hash-bound content-safe evidence, but it has not been executed on the required external
  host.
- [ ] **TLS termination:** production cookies are `Secure`. The production overlay must sit behind
  operator-managed HTTPS; the repository's port 8080 Nginx endpoint is the local/development
  acceptance endpoint and does not terminate TLS.
- [ ] **Real CRM/ERP:** intentionally deferred until a design partner identifies the actual system.

The product is a production-candidate implementation, not a released MVP, until the first three
release blockers above are closed. External write actions remain prohibited.

## Commercial product architecture alignment — 17 July 2026

The product is now treated as software sold and updated through isolated customer installations.
This does not introduce shared SaaS tenancy. The manager's `NEW_ARCHITECTURE_PLAN.md` and
`NEW_ARCHITECTURE.yaml` are the target platform family; this status file remains the truth about
what is executable today.

### Implemented or preserved

- [x] Single-company boundary is preserved per customer installation.
- [x] Local Docker Compose remains the executable reference deployment.
- [x] Vendor-controlled agent, capability, and workflow catalogs remain allowlisted and versioned.
- [x] Customer workflow customization is limited to draft/clone/edit/validate/dry-run/publish of
  safe definitions; arbitrary code and unrestricted plugins are unavailable.
- [x] OpenTelemetry/Jaeger content-safe tracing remains available as the current observability
  baseline.
- [x] Read-only external-system boundary remains enforced; MCP and write actions are not present.

### Not yet implemented or release-qualified

- [ ] A supported AWS runtime, IaC package, customer account/VPC ownership model, and TLS path are
  selected and exercised on a clean release host.
- [ ] The vendor-provided GPU server contract is defined: dedicated server versus isolated model
  process/queue, private connectivity, capacity, patching, model provenance, and incident ownership.
- [ ] Customer update, signed image promotion, migration, rollback, and support-telemetry package
  is implemented.
- [ ] Langfuse self-hosted integration and its content-safe retention/telemetry policy are not yet
  part of the release acceptance evidence.
- [ ] A first real CRM/ERP read-only connector has not been selected; MCP remains a future adapter
  boundary.
- [ ] Bounded task/round orchestration with dynamic workers is deliberately post-MVP and has no
  product implementation or qualification evidence.
- [ ] Diagnostic concurrency and starter capacity profiles for small companies are not yet a
  published product contract.

## Current verification evidence

- Backend suite: 88 tests; Ruff passes. The receipt integrity suite includes digest tampering,
  missing-member rejection, legacy receipt absence, and unknown-classification rejection.
- Frontend suite: 8 Vitest tests; production build passes.
- Ruff and Alembic drift: pass; migration head `20260713_0007`.
- Compose: base, development, production, cloud, observability, temporary model-download, and
  isolated browser-E2E configurations validate.
- Browser E2E: 5 model-independent Playwright tests pass against isolated empty volumes for truthful
  dashboard state, code-defined model-profile discovery, persisted setup/demo sync and Sources UI,
  Agent Registry create/publish, and workflow dry-run/publish/version/schedule management. Two
  additional opt-in suites cover real-model release acceptance and restored lexical-fallback state;
  both remain intentionally unchecked until release capacity exists.
- Live upgrade smoke: existing user-owned `growth-diagnostic` versions remained untouched while the
  reserved `builtin-growth-diagnostic:3` exact-agent-pinned workflow was seeded as published; API
  health is ok. Historical v2 is not selected by default.
- Latest safe qualification report: current persistent-workflow path, one failed attempt, 313.34
  seconds, `TimeoutError` at `company_agent`; Linux/x86-64 container, 12 CPUs, 7,902 MiB memory,
  Ollama context 8,192, no VRAM. It records workflow `qualification-local-balanced:1`, agent
  versions `3/3/3/2`, retrieval revision, policy revision, and effective-prompt hashes.
- Current release policy is `2026-07-15.2`; the validator rejects qualification evidence from any
  earlier revision. The `2026-07-15.1` 9B report above remains failure history, not current release
  qualification evidence.
- Final-image receipt smoke: each model prompt exposes at most three evidence IDs while the five
  calculation receipts bind 184, 183, 183, 400, and 258 complete verification members respectively;
  the inspection transaction was rolled back.
- Observability smoke: Jaeger v2 UI/API is reachable only in the explicit profile and receives
  `agi-control-plane` OTLP traces; the standard stack was restored afterward.
- No-egress: an HTTPS request from the default app container is blocked.
- Cloud-egress smoke: Squid 6.10 parses the checked-in policy; an `example.com` HTTPS tunnel is
  denied while Groq and Mistral HTTPS tunnels reach provider-auth responses through port 443 only.
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
