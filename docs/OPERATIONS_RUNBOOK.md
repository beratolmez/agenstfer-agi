# Operations Runbook

## Start and inspect

```bash
cp .env.example .env
docker compose up -d --build
docker compose ps
docker compose logs --tail=200 app web-proxy
```

Open `http://localhost:8080`; API documentation is at `/api/docs`. Use `/api/health` for service readiness and `/api/model/status` for model readiness.

## Model troubleshooting

If Ollama is reachable but the model is absent, test container DNS before pulling:

```bash
docker compose exec ollama getent hosts registry.ollama.ai
docker compose exec ollama ollama list
```

The product must not silently switch to cloud. To enable Groq or Mistral, configure the cloud profile explicitly and start the cloud Compose overlay. Confirm the provider/model with the structured-output probe before running a workflow.

## qmd

qmd is an optional disposable index. If it fails, knowledge search uses the lexical fallback. Rebuild qmd only from the approved active OKF revision; never treat its cache as backup data.

## Backup and restore

Back up PostgreSQL and the complete knowledge volume/repository together. Produce checksums, keep secrets outside the archive, and record application/database revisions. A backup is not accepted until restored into an empty installation and the diagnostic artifacts/citations are verified.

## Incident rules

- Disable cloud profiles immediately if unexpected egress or classification failure occurs.
- Do not copy raw prompts/source bodies into tickets or logs.
- Preserve audit records, workflow IDs, artifact hashes, and Git revisions.
- Reject or expire pending candidates if their evidence or base revision is no longer trustworthy.

