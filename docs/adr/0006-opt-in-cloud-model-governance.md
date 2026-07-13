# ADR-0006: Opt-in production cloud model governance

## Status

Accepted — 13 July 2026

## Decision

Local models remain the default, but an administrator may enable Groq or Mistral for production. Cloud enablement is never automatic fallback. It requires an explicit provider/model profile, allowlisted egress, a real structured-output probe, classification enforcement, redaction, and audit metadata.

`public` and policy-approved `internal` content may be sent after redaction. `confidential` and `restricted` content is blocked from cloud providers in MVP v0.1. Production secrets come from Docker/host secrets; development may use an ignored `.env` file.

## Consequences

Every run pins its exact provider and model. Failure of a local model cannot silently disclose content to a cloud service. Logs may contain provider, model, classification, hashes, token counts, and policy outcomes, but never API keys, prompt bodies, or source bodies.

