# Audited MVP Implementation Plan

Target: a production-candidate, single-company, self-hosted Growth Diagnostic product. Estimated remaining effort is 14–18 solo-developer weeks. The broader PRD is a post-MVP roadmap, not an instruction to add every module now.

## Status rules

- `docs/IMPLEMENTATION_STATUS.md` is the evidence-backed current-state record.
- A phase starts only after the previous exit gate passes.
- UI mock behavior, schema-only code, deterministic fixtures, and uncalled model factories are partial—not completed capabilities.
- Update status, tests, and relevant ADRs in the same change as a capability.

## Phase 0 — Truthful baseline and project memory

- [x] Secret-scan and commit the audited scaffold.
- [x] Add root engineering rules, status corrections, domain/evaluation/threat/operations/release documents, and ADRs 0005–0007.
- [x] Add cross-platform project verification scripts.
- [x] Create and validate the personal `agentic-growth-engineer` Codex skill.
- [x] Re-run the full baseline verification.
- [x] Commit Phase 0 documentation/tooling.

Exit: a new engineer can identify implemented, simulated, disabled, and missing behavior without reading source code.

## Phase 1 — Trustworthy platform foundation

- [x] Replace startup `create_all()` with mandatory explicit Alembic migrations.
- [x] Implement bootstrap/login/logout/current-user UI and API behavior.
- [x] Disable demo auth in standard Compose and reject default production secrets.
- [x] Protect non-public routes with session auth, roles, and CSRF.
- [x] Audit current material mutations and approval/authentication events.
- [x] Query PostgreSQL in readiness checks and report qmd/model readiness separately.
- [x] Return structured API errors with request IDs.

Exit: a clean deployment migrates, bootstraps one admin, enforces roles/CSRF, and records security-relevant operations.

## Phase 2 — Persistent ingestion, evidence, and OKF

- [x] Persist sources, mappings, sync runs, snapshots, artifacts, entities, facts, and evidence.
- [x] Add CSV/XLSX upload, discovery, preview, versioned mapping, and read-only sync APIs/UI.
- [x] Route the synthetic company through the same connector/mapping path.
- [x] Derive evidence hashes and exact locators from immutable snapshots.
- [x] Harden OKF import against traversal, symlinks, cumulative archive size, and decompression abuse.
- [x] Generate isolated Git-backed candidates and serialize authenticated merge into active `main`.
- [x] Rebuild qmd only after approved merge; preserve lexical fallback.

Exit: synchronized data becomes a conformant, traceable candidate bundle that can be approved, exported, and round-tripped.

## Phase 3 — Real Growth Diagnostic vertical slice

- Define typed Company Analysis, Opportunity Hypotheses, Evidence Review, and Diagnostic outputs.
- Expose only scoped knowledge/evidence/metric/candidate-write capabilities.
- Execute Pydantic AI through pinned Ollama, Groq, or Mistral profiles with no automatic fallback.
- Add a real structured-output probe and classification/cloud policy enforcement.
- Calculate metrics and scores from persisted data.
- Reject unsupported material or numerical claims.
- Persist exact agent/model/workflow versions, results, safe usage metadata, errors, and artifacts.
- Produce Markdown, print-ready HTML, and candidate OKF reports.

Exit: the Anka diagnostic is computed and model-assisted rather than returned from a static fixture.

## Phase 4 — Agent and workflow platform

- Add immutable published Agent, Capability, and Workflow versions with editable drafts.
- Keep capabilities and nodes code-defined; prohibit arbitrary code/plugins/network tools.
- Implement workflow CRUD/clone/validate/dry-run/publish/run APIs and UI.
- Persist run/step/approval history and use `Idempotency-Key`.
- Implement safe field/operator/value conditions and typed true/false branches.
- Complete DBOS retry, restart/resume, seven-day approval, rejection, and expiry behavior.
- Require authenticated Approver decisions with reasons and audit.
- Implement validated cron/timezone schedules with duplicate prevention.

Exit: users can safely edit, publish, execute, inspect, pause, approve, and resume a versioned workflow.

## Phase 5 — Complete user journey

- Persist every setup-wizard step and validated configuration.
- Replace Sources, Approval Center, Settings, and Opportunities placeholders.
- Drive dashboard/history from persisted runs.
- Navigate citations to exact source locations.
- Add candidate diff, decision, artifact download, and OKF export/import journeys.
- Add actionable degraded, retry, cancellation, empty, and error states.
- Keep Turkish-first UI with normal i18n structure and accessible keyboard behavior.

Exit: onboarding through approved report works without a terminal.

## Phase 6 — Security, operations, and release

- Keep cloud disabled by default; enforce allowlisted egress, redaction, classification, and content-safe audit.
- Use Docker/host secrets for production model credentials.
- Add OpenTelemetry metrics/traces without sensitive payloads.
- Test PostgreSQL + knowledge Git backup and clean restore on Linux and from PowerShell development workflows.
- Pin images/dependencies, generate an SBOM, scan vulnerabilities, and test clean Linux installation.
- Pass the threat model, evaluation plan, release checklist, browser E2E, and recovery drills.

Exit: the release checklist passes on a clean and a restored installation.

## Public interface direction

Keep `/api` for v0.1. Add resource APIs for auth, models/probes, sources/mappings/syncs, knowledge/evidence/candidates, agents/capabilities, workflows/versions/schedules, runs/steps/artifacts, and approvals. Production runs reference immutable published versions; only draft dry-run accepts an inline definition. Keep current dashboard/diagnostic routes as deprecated persisted views through v0.1.

## Post-MVP sequence

1. Real design partner and first read-only CRM/ERP connector.
2. Website, competitor, and market-signal ingestion.
3. Lead discovery/enrichment and evidence-backed scoring.
4. Campaign, social, AEO, battlecard, and event intelligence.
5. Financial/ERP, CRM hygiene, and cybersecurity insight.
6. Only after new consent, legal, threat-model, and ADR gates: controlled messaging, calling, and external write actions.
