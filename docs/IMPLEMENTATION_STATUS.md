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
- [x] Growth metrics and opportunity scores are computed from persisted canonical entities; changing persisted inputs changes the metrics.
- [x] Four typed Pydantic AI agents run sequentially with capability-scoped tools and a pinned model profile; no automatic provider fallback exists.
- [x] Every material/numerical claim passes an Evidence Reviewer gate against persisted evidence before a candidate is created.
- [x] Diagnostic run/step versions, input hashes, outputs, safe errors, token usage, evidence IDs, Markdown/HTML artifacts, and OKF candidate are persisted.
- [x] Model structured-output probing is a real provider call and is exposed in the setup UI.
- [x] Diagnostic run list/detail/artifact APIs exist; the dashboard delegates to the latest successful persisted diagnostic.

## Partial — do not represent as complete

- [ ] **Release model acceptance:** real Pydantic AI execution exists and is covered with typed test models, but no release-enabled provider can be live-verified on the audited machine because `qwen3.5:9b` is not installed and no governed cloud key is configured.
- [ ] **Fallback dashboard:** until the first successful model-assisted run, `GET /api/dashboard` intentionally shows the legacy deterministic preview; `POST /api/diagnostics/run` never falls back to it.
- [ ] **Operational state:** ingestion/evidence/OKF state is populated and failed run attempts are persisted, but no first administrator exists yet and published workflow/approval histories remain incomplete.
- [ ] **Workflow product:** editor validation calls the API; Save, Dry-run, Publish, Run, history, and versions are not functional end to end.
- [ ] **Durability:** DBOS receives approval messages, but application run/step/approval records and restart acceptance tests do not exist.
- [ ] **Approval:** the current workflow approval route is role-protected and audited, but approval records/history and the Approval Center are not implemented.
- [ ] **Ingestion breadth:** demo and bounded CSV/XLSX sources work; real CRM/ERP connectors intentionally wait for a design partner.
- [ ] **Golden evaluation:** the Evidence Reviewer gate is implemented, but planted-opportunity, repeated-run, and release-profile quality thresholds have not been executed against a real release model.
- [ ] **Approval Center:** OKF candidate decision APIs work, but the dedicated review/diff UI and persisted workflow approvals are Phase 4/5 work.
- [ ] **Setup:** most wizard steps are previews and are not persisted.
- [ ] **Operations:** backup scripts exist for Linux but have no restore drill, PowerShell wrapper, encryption policy, or release evidence.

## Current verification results

- Backend: 30 tests passed.
- Frontend: 3 tests passed.
- Ruff: passed.
- Frontend production build: passed.
- Base and cloud Compose configuration: passed.
- Migration drift: no new upgrade operations detected.
- Live health: API, PostgreSQL query, OKF, and Ollama process reported available; qmd is unavailable and lexical fallback is active.
- Live Phase 2 drill: 1,783 records synchronized into 3 snapshots; a citation resolved to CRM row 18; the candidate was approved and active knowledge advanced.
- Live Phase 3 failure drill: a missing-model diagnostic persisted a failed run at `model-readiness`, returned HTTP 409, and did not silently fall back.
- Typed Phase 3 integration: all four Pydantic AI agents, evidence gate, persisted five-step trace, three artifacts, idempotency, and rejection-without-candidate passed against the full runtime using typed test models.
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

Phase 4 — immutable Agent/Capability/Workflow versions and a durable workflow platform. Phase 3 provider-specific golden acceptance remains a release gate because this machine has no ready model.

## Deliberately outside the MVP

External write-back, lead scraping, outbound/inbound calls, financial automation, cybersecurity operations, and competitor automation remain disabled. They require separate policy, threat-model, evidence, consent, and approval decisions.
