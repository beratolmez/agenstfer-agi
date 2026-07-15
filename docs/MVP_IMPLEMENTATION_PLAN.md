# Audited MVP Implementation Plan

Target: a production-candidate, single-company, self-hosted Growth Diagnostic product. The broader
PRD remains a post-MVP roadmap.

## Status rules

- `IMPLEMENTATION_STATUS.md` is the evidence-backed current-state record.
- UI-only behavior, schemas, model factories, and mocked provider output are not release completion.
- Update status, tests, threat model, and relevant ADRs with each material capability.
- External write actions are prohibited throughout MVP v0.1.

## Phase 0 — Truthful baseline and project memory

- [x] Commit and secret-scan the scaffold.
- [x] Add root engineering rules, domain/evaluation/threat/operations/release documents, ADRs
  0005–0007, project checks, and the validated Codex project skill.

Exit gate: passed.

## Phase 1 — Trustworthy platform foundation

- [x] Mandatory explicit Alembic migrations.
- [x] Bootstrap/login/logout/current user, users/roles, session auth, CSRF, role enforcement, audit,
  request IDs, structured errors, and truthful health.
- [x] Standard authentication enabled; development bypass isolated; production weak secrets rejected.

Exit gate: passed in automated tests and an isolated production bootstrap drill.

## Phase 2 — Persistent ingestion, evidence, and OKF

- [x] Persist sources, mappings, syncs, immutable snapshots, artifacts, canonical context, and exact
  evidence locators.
- [x] Route demo and CSV/XLSX data through the same read-only pipeline.
- [x] Safe OKF import/export and approval-controlled Git candidate lifecycle.
- [x] qmd-after-approval policy and lexical fallback.

Exit gate: passed with a 1,783-record live round-trip and exact citation resolution.

## Phase 3 — Real Growth Diagnostic vertical slice

- [x] Typed Company Analysis, Opportunity Hypotheses, Evidence Review, and OKF outputs.
- [x] Capability-scoped tools, explicit provider profiles, deterministic metrics/scores, evidence
  gate, persisted trace, and Markdown/HTML/OKF artifacts.
- [x] Real model probe and no automatic fallback.
- [x] Code-defined profile discovery and selected-profile pinning to an immutable workflow version;
  the compatibility diagnostic endpoint delegates to the persisted DBOS runtime.
- [ ] Qualify at least one real provider profile with the executable golden suite.

Implementation gate: passed with Pydantic AI typed test models, deterministic aggregate receipts,
and claim-complete reviewer batching. Release gate: blocked because no provider profile has passed
qualification; the installed 9B profile passes isolated nodes but failed its latest full golden run
at Company Analyst after its current production-path timeout budget was exhausted (313.34 seconds
total). A preceding historical full attempt had reached Evidence Reviewer before failing after
939.27 seconds.

## Phase 4 — Functional agent and workflow platform

- [x] Immutable Agent/Capability/Workflow versions and editable drafts.
- [x] Code-defined capabilities; no custom code/plugin/unrestricted network nodes.
- [x] Admin Agent Registry create/clone/edit/save/publish/version-detail flow, strict typed contract
  allowlists, server-controlled version lineage, and immutable system-policy composition.
- [x] CRUD/clone/validate/dry-run/publish/run, safe conditions/branches, schedules, idempotency, and
  persisted run/step/approval/artifact histories. Inline draft dry-run is a labeled deterministic
  simulation; only a published run invokes configured agents.
- [x] DBOS retry/recovery wrapper, durable approval receive, seven-day expiry, authenticated reasoned
  decisions, and restart-safe PostgreSQL checkpoints.
- [x] Cancellation first cancels the DBOS workflow and changes application state only on success;
  retry always references the original immutable published workflow version.
- [x] React Flow actions, workflow selection/version history, schedule create/enable/disable, run
  trace, and Agent/Capability registry management use real APIs. Published/history views are read-only.

Exit gate: implementation passed; real-provider approval wait/resume remains part of final E2E.

## Phase 5 — Complete user journey

- [x] Persist all setup steps and validated configuration.
- [x] Replace Sources, Approval Center, Settings, and Opportunities placeholders.
- [x] Persisted dashboard/history, exact citation navigation, candidate diff/decision/export, report
  download, degraded/error/retry/cancel states, Turkish-first i18n boundary, and responsive controls.
- [x] Remove the synthetic dashboard fallback; no model-assisted result is shown before a persisted
  evidence-reviewed run exists.

Exit gate: UI/API functionality passed; complete happy path awaits a qualified model.

## Phase 6 — Security, operations, and release engineering

- [x] Default-deny cloud policy, allowlisted egress, classification/redaction, content-safe model
  audit, host/Docker secrets, and no-egress check.
- [x] Content-safe OpenTelemetry/Jaeger overlay.
- [x] PostgreSQL application + DBOS system + knowledge Git backup/restore on PowerShell and Linux.
- [x] Digest-pinned production images, pinned qmd, CycloneDX SBOM, and zero fixable HIGH/CRITICAL
  Trivy findings in the audited image.
- [x] Isolated empty-volume production Compose migration/bootstrap/auth drill.
- [x] Isolated model-independent Playwright coverage for truthful dashboard, persisted demo sync,
  Sources UI, and safe workflow clone/dry-run behavior.
- [x] Opt-in real-model and restored-state Playwright contracts plus a Linux x86-64 release rehearsal
  orchestrator. The rehearsal coordinates same-run agent/approval restarts and fail-closed,
  hash-bound evidence validation. These are executable gates, not completion evidence.
- [x] Qualification executes a profile-pinned immutable clone of the current published workflow and
  records content-safe workflow/agent/policy/effective-prompt provenance; legacy synchronous reports
  fail independent release-evidence validation.
- [ ] Run full browser E2E with a qualified model on a separate clean Linux x86-64 host.
- [ ] Run qmd loss/rebuild and final 20-run model evaluation on that host.

Exit gate: not yet passed; see release blockers in `IMPLEMENTATION_STATUS.md`.

## Remaining release sequence

1. Keep the installed `qwen3.5:9b` only as a development profile. Its probe and isolated v3 agent/
   receipt-review calls pass, but the full golden diagnostic still fails and no 20-run qualification
   exists on this CPU-bound host. Native JSON Schema and ToolOutput experiments were also unreliable;
   do not promote them or weaken evidence contracts to make 9B pass.
2. Qualify `qwen3.5:27b` on suitable hardware or configure one governed Groq/Mistral secret, then
   pass the real structured-output probe and 20-run golden qualification.
3. Execute onboarding → sync → diagnostic → citation → approval → active OKF export in the browser.
4. Restart during execution and approval; verify DBOS resumes the same run ID.
5. Repeat install, E2E, qmd rebuild, SBOM/scan, backup, and clean restore on Linux x86-64.
6. Update the release checklist and tag v0.1.0 only when every required gate is checked.

## Post-MVP sequence

1. Design partner and first read-only CRM/ERP connector.
2. Approved website/competitor/market ingestion.
3. Lead discovery/enrichment and evidence-backed scoring.
4. Campaign/social/AEO/battlecard/event intelligence.
5. Financial/ERP, CRM hygiene, and cybersecurity insight.
6. Only after new consent, legal, threat-model, rollback, and ADR gates: controlled external writes,
   messaging, and calling.
