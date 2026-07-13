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

## Partial — do not represent as complete

- [ ] **Model execution:** model status is not ready on the audited machine; workflow agent nodes do not call Pydantic AI.
- [ ] **Diagnostic:** recommendations are deterministic fixtures rather than computed agent results.
- [ ] **Persistence:** PostgreSQL tables exist, but the audited database has zero users, evidence items, canonical records, workflow definitions/runs, approvals, and audit events.
- [ ] **Authentication:** bootstrap/login primitives exist, but standard Compose currently inherits demo auth bypass and the web app has no real auth journey.
- [ ] **Workflow product:** editor validation calls the API; Save, Dry-run, Publish, Run, history, and versions are not functional end to end.
- [ ] **Durability:** DBOS receives approval messages, but application run/step/approval records and restart acceptance tests do not exist.
- [ ] **Approval:** the current workflow approval route is not role-protected or audited, and the Approval Center is a placeholder.
- [ ] **Ingestion:** file connector code exists, but there are no source/upload/mapping/sync APIs or UI.
- [ ] **Evidence:** demo evidence is not persisted and its locators/hashes are not derived from the stored raw snapshot.
- [ ] **OKF approval:** the compiler writes the bundle directly; isolated candidates and approval-controlled merge are missing.
- [ ] **Setup:** most wizard steps are previews and are not persisted.
- [ ] **Operations:** backup scripts exist for Linux but have no restore drill, PowerShell wrapper, encryption policy, or release evidence.

## Current verification results

- Backend: 16 tests passed.
- Frontend: 1 test passed.
- Ruff: passed.
- Frontend production build: passed.
- Base and cloud Compose configuration: passed.
- Live health: API, PostgreSQL configuration, OKF, and Ollama process reported available.
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

Phase 1 — trustworthy platform foundation. It cannot be marked complete until migrations, auth/RBAC/CSRF, audit, database readiness, and structured errors pass their exit gate.

## Deliberately outside the MVP

External write-back, lead scraping, outbound/inbound calls, financial automation, cybersecurity operations, and competitor automation remain disabled. They require separate policy, threat-model, evidence, consent, and approval decisions.
