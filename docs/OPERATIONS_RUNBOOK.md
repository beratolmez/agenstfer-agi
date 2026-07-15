# Operations Runbook

## Local start

```powershell
Copy-Item .env.example .env
docker compose up -d --build
docker compose ps
```

Open `http://localhost:8080`. Standard Compose enforces authentication; use
`docker-compose.dev.yml` only for an explicit development bypass.

## Production start

Production cookies are `Secure`; terminate HTTPS in an operator-managed reverse proxy before port
8080. Generate ignored host secret files and start the production overlay:

```powershell
.\scripts\initialize-secrets.ps1
docker compose -f docker-compose.yml -f docker-compose.production.yml up -d --build
```

Linux uses `./scripts/initialize-secrets.sh`. Store the bootstrap token securely until the first admin
is created. Do not commit `.env`, `.secrets/`, backups, or generated release reports.

## Model profiles

Local model:

```powershell
docker compose exec ollama ollama list
.\scripts\pull-model.ps1 -Model qwen3.5:9b
```

The helper temporarily attaches only Ollama to `model-download`, pulls the allowlisted model, and
recreates Ollama on the internal-only network in a `finally`/trap handler. Linux uses
`./scripts/pull-model.sh qwen3.5:9b`. If corporate DNS still blocks the registry, use an approved
network path or a governed cloud profile; do not weaken the permanent Docker network boundary.

The constrained reference host uses `OLLAMA_CONTEXT_LENGTH=8192` and `OLLAMA_NUM_PARALLEL=1` from
`.env.example`. Confirm the effective context and residency with:

```powershell
docker compose exec ollama ollama ps
```

Increasing context consumes memory; validate host capacity before changing it. These settings do not
make a profile supported. The installed 9B profile failed the latest complete golden attempt and must
remain development-only until the full 20-run suite passes.

If the Ollama registry is unavailable, do not silently switch provider. For governed cloud use:

1. Put only the key in `.secrets/cloud_model_api_key`.
2. Set `AGI_CLOUD_PROVIDER=groq` or `mistral` and `AGI_MODEL_PROFILE=cloud-balanced` in `.env`.
3. Start base + production + cloud overlays with `--profile cloud`.
4. Run the real model probe and golden evaluation.

Only Groq/Mistral hosts pass Squid. `confidential` and `restricted` evidence remains cloud-blocked.

## qmd and observability

qmd is disposable and never backup state. Start with `--profile search`; approved active revisions
request reindex, while qmd failure falls back to lexical search.

```powershell
docker compose -f docker-compose.yml -f docker-compose.observability.yml --profile observability up -d
```

Jaeger is at `http://localhost:16686`. OTLP telemetry contains HTTP route templates, method, status,
duration, and request ID—not payloads or secrets. Provider/model/classification/redaction metadata
is persisted separately on content-safe workflow step rows.

## Backup and restore

Backups briefly stop the app to prevent concurrent DBOS or knowledge writes, then capture a
consistent triple: application PostgreSQL, `${POSTGRES_DB}_dbos_sys`, and the complete knowledge Git
volume. The app is health-checked before the script returns.

```powershell
.\scripts\backup.ps1
.\scripts\restore.ps1 .\backups\<timestamp>
```

```bash
./scripts/backup.sh
./scripts/restore.sh ./backups/<timestamp>
```

Restore verifies SHA-256 and archive paths, stops the app to prevent concurrent DBOS writes, restores
both databases and knowledge, then restarts the app. A backup is accepted only after a restore drill.
Encrypt and move backups using the operator's storage policy; encryption keys stay outside archives.

## Release evidence

```powershell
.\scripts\project-check.ps1 -Live
.\scripts\verify-no-egress.ps1
.\scripts\release-scan.ps1
.\scripts\browser-e2e.ps1
.\scripts\qualify-model.ps1 -Profile local-balanced -Attempts 20
```

The ignored qualification JSON records safe per-attempt duration, token totals, claim coverage,
unsupported numerical-claim count, failure class/stage, CPU/memory, and available Ollama runtime
metadata. It must never include prompts, response bodies, evidence excerpts, or secrets.

`release-scan` creates an ignored CycloneDX SBOM and Trivy report. The Trivy image itself is pinned by
digest. `browser-e2e` uses an isolated Compose project, empty volumes, loopback port 18080, explicit
development authentication bypass, and always removes its containers/volumes. It covers only
model-independent flows; it does not satisfy the real-model happy-path release gate. On Linux,
install the pinned Playwright Chromium dependencies first, then run `./scripts/browser-e2e.sh`.
Repeat the same checks on the release Linux host.

Run the real-model journey only against an explicitly disposable authenticated installation. Put
password/bootstrap values in process environment variables so they do not appear in command-line
arguments:

```powershell
$env:AGI_E2E_ADMIN_PASSWORD = "<secret>"
$env:AGI_E2E_BOOTSTRAP_TOKEN = "<one-time-secret>"
.\scripts\browser-real-model-e2e.ps1 -BaseUrl http://127.0.0.1:8080 `
  -AdminEmail release-admin@example.test -ModelProfile cloud-balanced -ConfirmDisposable
```

Non-loopback targets must use HTTPS. The suite changes setup state, sources, workflow versions,
runs, approvals, and active OKF knowledge. It requires DBOS: approval submission must first return
`decision_submitted`, then the same run must complete.

On the required separate Linux x86-64 release host, use the composed rehearsal after configuring
HTTPS and one approved model profile:

```bash
export AGI_E2E_ADMIN_PASSWORD='<secret>'
./scripts/release-rehearsal.sh --base-url https://agi.example.internal \
  --admin-email release-admin@example.test --model-profile cloud-balanced \
  --attempts 20 --confirm-disposable
```

The rehearsal owns the dedicated `agi-release-rehearsal` Compose project and deletes only its
volumes. It starts a restart watchdog before the real-model browser journey. The watchdog interrupts
the exact app container during a persisted agent step and again during the same run's pending approval,
then requires that run to complete after the browser decision. The browser tolerates only transient
restart failures and waits for a run-ID-bound healthy marker before approval.

The rehearsal writes a content-safe ignored v2 manifest under `artifacts/release/rehearsal-*`.
Qualification JSON is independently checked for at least 20 attempts, all evaluation thresholds,
attempt/result consistency, and forbidden content-bearing fields. Restart evidence is checked for the
same workflow run and container across both interruptions. The manifest binds qualification, restart,
SBOM, Trivy, and backup-checksum artifacts by SHA-256. A zero exit cannot produce a passing manifest
when a required step or artifact is missing. Prompts, source bodies, evidence excerpts, passwords,
bootstrap tokens, and provider keys are prohibited from these evidence files.

Backup and restore restart the exact app container that was stopped. They do not run a new
`docker compose up` with base configuration, so a production/cloud overlay cannot be silently
replaced during a recovery drill.

## Incident rules

- Disable cloud overlays immediately after unexpected egress/classification/redaction behavior.
- Do not copy prompts, source bodies, evidence excerpts, cookies, or secrets into logs/tickets.
- Preserve run IDs, safe audit rows, artifact hashes, DBOS status, and OKF Git revisions.
- Reject/expire candidates whose evidence or base revision is no longer trustworthy.
- Restore application DB, DBOS DB, and knowledge from the same backup generation.
