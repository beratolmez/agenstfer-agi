# Implementation Status

Last verified: 13 July 2026
Baseline commit: `587d312` (`chore: capture initial MVP scaffold`)

This is the authoritative statement of what the repository actually does. A checked item has been verified in code or by the commands at the end of this document. The source PRD and manager architecture remain unchanged vision inputs.

## Verified foundation

- [x] FastAPI and the built React application are served through Nginx at `http://localhost:8080`.
- [x] Base Compose starts `app`, PostgreSQL, Ollama, and `web-proxy` on internal/ingress networks.
- [x] Optional qmd, Jaeger, and allowlisted cloud-egress services are defined.
- [x] The synthetic Anka dataset has the planned record counts.
- [x] Read-only connector contracts, demo/tabular connectors, and immutable raw-vault primitives exist.
- [x] OKF 0.1 parse/write, tolerant metadata round-trip, validation, index/log, ZIP round-trip, links/backlinks, and lexical fallback exist.
- [x] Four agent specifications and an Ollama/Groq/Mistral model factory scaffold exist.
- [x] A typed workflow graph, validator, deterministic local interpreter, and DBOS interpreter skeleton exist.
- [x] Dashboard, Knowledge Explorer, setup shell, and React Flow editor render.
- [x] The audited scaffold is committed to Git.
- [x] Root engineering rules, project check scripts, required governance documents, and ADRs 0005–0007 exist.
- [x] The personal `agentic-growth-engineer` Codex skill passes standard validation.
- [x] Explicit Alembic migration replaces application startup `create_all()` and upgrades both empty and known legacy scaffold databases.
- [x] Standard Compose enforces session authentication; demo bypass requires the explicit development overlay.
- [x] The web app renders first-admin bootstrap or login before protected product surfaces.
- [x] Session CSRF, role dependencies, production-secret validation, request IDs, structured errors, and current mutation audit hooks exist.
- [x] Readiness executes `SELECT 1` against PostgreSQL and reports Ollama/qmd separately.
- [x] Source, mapping, sync-run, immutable snapshot, artifact, entity, fact, and evidence state is persisted.
- [x] CSV/XLSX upload, schema preview, versioned mapping, classification, read-only sync APIs, and Sources UI work end to end.
- [x] The Anka fixture travels through the connector pipeline into three logical sources; the live audit contains 1,783 canonical entities and evidence items.
- [x] Evidence resolves to an immutable snapshot, exact sheet/row/external ID locator, excerpt, and verified content hash.
- [x] OKF import rejects traversal, symlinks, Git internals, non-Markdown payloads, excessive entries, and cumulative expanded size.
- [x] OKF candidates are isolated Git worktrees with seven-day expiry; approval fast-forwards active `main`, rejection leaves it unchanged, and only approval requests qmd reindexing.
- [x] Active OKF export/import preserves unknown types and metadata through an approval-controlled candidate round trip.

## Partial — do not represent as complete

- [ ] **Model execution:** model status is not ready on the audited machine; workflow agent nodes do not call Pydantic AI.
- [ ] **Diagnostic:** recommendations are deterministic fixtures rather than computed agent results.
- [ ] **Operational state:** ingestion/evidence/OKF state is populated, but no first administrator exists yet and workflow definitions/runs/approval histories remain empty.
- [ ] **Workflow product:** editor validation calls the API; Save, Dry-run, Publish, Run, history, and versions are not functional end to end.
- [ ] **Durability:** DBOS receives approval messages, but application run/step/approval records and restart acceptance tests do not exist.
- [ ] **Approval:** the current workflow approval route is role-protected and audited, but approval records/history and the Approval Center are not implemented.
- [ ] **Ingestion breadth:** demo and bounded CSV/XLSX sources work; real CRM/ERP connectors intentionally wait for a design partner.
- [ ] **Evidence review:** source evidence is real and resolvable, but agent-generated claims are not yet reviewed against it by a model-backed Evidence Reviewer.
- [ ] **Approval Center:** OKF candidate decision APIs work, but the dedicated review/diff UI and persisted workflow approvals are Phase 4/5 work.
- [ ] **Setup:** most wizard steps are previews and are not persisted.
- [ ] **Operations:** backup scripts exist for Linux but have no restore drill, PowerShell wrapper, encryption policy, or release evidence.

## Current verification results

- Backend: 25 tests passed.
- Frontend: 3 tests passed.
- Ruff: passed.
- Frontend production build: passed.
- Base and cloud Compose configuration: passed.
- Migration drift: no new upgrade operations detected.
- Live health: API, PostgreSQL query, OKF, and Ollama process reported available; qmd is unavailable and lexical fallback is active.
- Live Phase 2 drill: 1,783 records synchronized into 3 snapshots; a citation resolved to CRM row 18; the candidate was approved and active knowledge advanced.
- Browser QA: bootstrap gate and the populated Sources screen rendered at `localhost:8080`; the Sources screen showed 1,370 CRM, 412 ERP, and 1 strategy record.
- Model readiness: false because the configured local model is not installed.

Run the same checks with:

```powershell
.\scripts\project-check.ps1 -Live
```

or:

```bash
./scripts/project-check.sh --live
```

## Active phase

Phase 3 — real, model-assisted Growth Diagnostic vertical slice.

## Deliberately outside the MVP

External write-back, lead scraping, outbound/inbound calls, financial automation, cybersecurity operations, and competitor automation remain disabled. They require separate policy, threat-model, evidence, consent, and approval decisions.
