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

## Customer product deployment

The product is delivered as one isolated installation per company. Before a customer rollout, record
whether the deployment is local private, managed AWS private, customer AWS private, or split private.
Do not combine Compose, ECS, EKS, and on-prem inference assumptions in one undocumented profile.

For an AWS deployment, document the customer account/VPC owner, private subnets, TLS terminator,
RDS/object-storage backup owner, image registry, secret store, and rollback version. Only the approved
ingress is public. PostgreSQL, the model service, raw vault, and observability services remain private.

The default commercial model server is a vendor-provided GPU server. Use the approved same-private-
VPC, private-service-link/VPN, or outbound-inference-gateway pattern. Do not publish Ollama or vLLM
on a public address, and do not enable automatic provider fallback. Record whether the customer has a
dedicated GPU server or a dedicated isolated model process/queue; shared GPU execution is not an MVP
default.

## Product updates

1. Verify the signed image/package and compatible migration set.
2. Run a fresh application, DBOS, knowledge, and observability backup.
3. Confirm model profile, data classification policy, and deployment manifest.
4. Apply the update during a controlled maintenance window.
5. Run migrations, health checks, authentication, evidence-resolution, workflow-start, and trace
   smoke tests.
6. Keep the prior image and backup available until the customer accepts the release.
7. Roll back the complete compatible set when a migration or runtime check fails.

Vendor support should use the content-safe release evidence and operational hashes. Raw prompts,
source bodies, evidence excerpts, secrets, and contact identifiers must not be copied into tickets.

## Langfuse profile

OpenTelemetry remains the instrumentation boundary. When the customer enables Langfuse, deploy it in
the same private environment or an explicitly approved isolated network. Configure retention, RBAC,
backup, and self-hosted telemetry according to the customer policy. Verify that traces contain only
provider/model, versions, durations, token totals, retry/validation outcomes, evidence counts, and
safe hashes. Jaeger remains the minimal fallback when Langfuse is unavailable.

## GPU server operations

The vendor owns model image/model-file provenance, GPU driver/runtime compatibility, capacity,
patching, health checks, and incident response for vendor-provided GPU servers. A customer deployment
must identify its GPU server or isolated model queue, region, model profile, maximum concurrent model
requests, and data-retention policy. Model downloads and upgrades are controlled operations and are
never performed by an agent.

## Capacity and concurrency

Small-company installations may have multiple concurrent browser users, but the default local model
profile uses one parallel inference request. Until a queue/worker capacity profile is released, run
one heavy Growth Diagnostic per installation and reject or defer overlapping starts. Candidate merge
remains serialized. A future bounded worker orchestrator must define its own maximum workers, rounds,
token budget, and recovery policy before enablement.

## Release evidence

```powershell
.\scripts\project-check.ps1 -Live
.\scripts\verify-no-egress.ps1
.\scripts\release-scan.ps1
.\scripts\browser-e2e.ps1
.\scripts\qualify-model.ps1 -Profile local-balanced -Attempts 20
```

The harness clones/publishes the current built-in workflow, pins the selected profile and exact agent
versions, and runs the same persistent interpreter used by production. The ignored qualification JSON
records workflow/agent identity, per-attempt retrieval revisions, policy revision, effective-prompt
hashes, safe per-attempt duration, token totals, claim coverage, unsupported numerical-claim count,
failure class/stage, CPU/memory, and available Ollama runtime metadata. It must never include prompts,
response bodies, evidence excerpts, or secrets.

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
Qualification JSON is independently checked for the published persistent-workflow path, exact
workflow/agent/policy provenance, at least 20 attempts, all evaluation thresholds, attempt/result
consistency, and forbidden content-bearing fields. Restart evidence is checked for the
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
