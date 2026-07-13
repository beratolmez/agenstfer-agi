# MVP Release Checklist

## Build and migration

- [ ] Clean Linux x86-64 host starts the stack from documented commands.
- [ ] Alembic upgrades an empty database and the previous released revision.
- [ ] Backend lint/tests and frontend tests/build pass.
- [ ] Base and opt-in cloud Compose configurations validate.

## Functional journey

- [ ] Admin bootstrap closes after first use and roles are enforced.
- [ ] A release-qualified model passes a real structured-output probe.
- [ ] Demo data uses connector, mapping, persistence, and evidence pipelines.
- [ ] Pydantic AI and DBOS produce a persisted Growth Diagnostic.
- [ ] Material citations open exact immutable source locators.
- [ ] Candidate approval merges; rejection leaves active knowledge unchanged.
- [ ] Workflow edit, validate, dry-run, publish, run, pause, resume, and history work.
- [ ] OKF export/import preserves unknown types and metadata.

## Quality and security

- [ ] All gates in `EVALUATION_PLAN.md` pass for every release-enabled profile.
- [ ] All negative cases in `THREAT_MODEL.md` pass.
- [ ] Default deployment has no unexpected egress.
- [ ] Logs contain no secrets, prompts, source bodies, or evidence excerpts.
- [ ] Dependency/image scan and SBOM review pass or have documented accepted risk.

## Recovery and handoff

- [ ] Backup restores into an empty installation with verified hashes.
- [ ] Restart during a step and approval resumes idempotently.
- [ ] Operations runbook matches the released deployment.
- [ ] `IMPLEMENTATION_STATUS.md`, architecture, OpenAPI, and ADRs match the release.

