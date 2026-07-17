# MVP Threat Model

## Protected assets

Company source content, credentials, personal/contact data, canonical context, OKF history, prompts, model configuration, workflow/approval state, audit integrity, and backups.

## Trust boundaries

1. Browser to Nginx/FastAPI.
2. FastAPI to PostgreSQL, raw vault, Git bundle, Ollama, and qmd.
3. Optional FastAPI to allowlisted cloud providers through the egress gateway.
4. Uploaded files and document text entering trusted processing as untrusted data.

The commercial target adds three explicit boundaries:

5. Customer deployment to vendor update/support channels.
6. AWS control plane to a vendor-operated private GPU or inference gateway.
7. Application telemetry to Langfuse or Jaeger.

## Mandatory controls

- Session authentication, CSRF, role enforcement, production Secure cookies behind HTTPS,
  bootstrap closure, and audit.
- Internal Docker network; only ingress proxy publishes a host port.
- Explicit model installation grants temporary outbound access only to Ollama and restores its
  internal-only network even after pull failure.
- Connector and agent capability allowlists; no arbitrary code or unrestricted URL tools.
- Immutable snapshots, path confinement, archive cumulative-size limits, and symlink rejection.
- Aggregate metric receipts are content-addressed and bind every member evidence ID/snapshot/excerpt/classification
  hash. Resolution must reject a changed receipt, missing member, nested derived member, or digest
  mismatch before the value reaches Evidence Reviewer. A numerical claim without a receipt must not
  fall back to representative raw rows; unknown evidence classifications block receipt creation.
- HTML export escaping. Formula-like imported cells are flagged as untrusted; any future CSV export
  must escape formula prefixes.
- Prompt-injection separation: source content cannot modify system policy or tool scope. The model
  gateway appends an immutable control-plane policy after every versioned editable agent instruction;
  even an administrator-authored prompt cannot reclassify source text as instructions, expand
  capabilities, authorize external actions, or invent evidence IDs.
- Agent and workflow publication revalidates code-defined model/output/capability bindings. New
  agent IDs start at version 1 and later versions are created only by cloning, so client-supplied
  version numbers cannot forge history.

## Commercial deployment threats

- **Cross-customer data leakage:** every customer receives isolated database, knowledge, model
  secret, and observability storage. Shared SaaS tenancy is not assumed.
- **Malicious or unsafe update:** update packages are versioned and signed; backup, migration,
  health-check, and rollback steps run before a customer deployment is changed.
- **Support-channel leakage:** vendor support receives content-safe hashes and operational metadata
  by default. Raw prompts, source bodies, evidence excerpts, and secrets require explicit customer
  approval and are not part of standard telemetry.
- **Public inference endpoint:** Ollama/vLLM is private-only. AWS-to-vendor-GPU inference uses the
  selected private VPC, VPN, private service link, or outbound gateway pattern; public model ports
  are prohibited.
- **Shared GPU cross-customer leakage:** the MVP prefers a dedicated GPU server or a dedicated
  model process/queue per customer. Shared GPU execution requires tenant-aware routing, cache and
  memory isolation, quotas, encrypted job/result handling, noisy-neighbor controls, and a new review.
- **Observability leakage:** Langfuse and Jaeger receive redacted metadata only. Retention, RBAC,
  backup, and self-hosted telemetry settings are reviewed before release.
- **Dynamic worker escalation:** a bounded task orchestrator can select only code-defined workers,
  tools, budgets, rounds, and data scopes. It cannot create arbitrary workers, call unrestricted MCP,
  execute code, or perform writes.

## Required deployment review

Before a customer production rollout, record the AWS account/VPC owner, inference network pattern,
TLS terminator, backup/restore owner, update/rollback procedure, Langfuse/Jaeger retention, support
telemetry policy, and maximum diagnostic concurrency. Changes require a deployment review and, when
the trust boundary changes, a new ADR.
- Classification and redaction before cloud calls. Because the MVP diagnostic computes aggregate
  metrics across the complete persisted canonical context, the model-call classification is the
  highest classification in that canonical/evidence scope; any `confidential` or `restricted` member blocks
  the cloud call before prompt transmission. The final model-gateway boundary also reapplies contact
  identifier redaction and rejects a local/cloud tool-boundary mismatch.
- Installation configuration accepts only code-defined model profiles, source modes, locales, and
  bounded company fields. A UI-provided provider URL, model identifier, or secret is never trusted.
- Compose allowlists application environment variables. Cloud API keys are mounted only as the
  cloud-profile secret file and are never inherited by PostgreSQL or the base app environment.
- Do not log secrets, prompts, source bodies, or evidence excerpts.
- Release evidence must reject content-bearing secret/prompt/source fields, independently validate
  model/restart claims, require the published persistent-workflow qualification path, bind exact
  agent versions plus effective-prompt hashes/policy revision, and hash-bind required artifacts before
  a rehearsal can report success.
- Idempotent workflows and approvals; stale/replayed decisions fail closed.
- Cancellation changes application/approval/candidate state only after DBOS confirms cancellation;
  retry cannot substitute a newer workflow for the run's pinned immutable version.
- Approval-controlled OKF merge and conflict detection.

## Required negative tests

Authentication bypass, missing/wrong role, CSRF, session fixation, prompt injection, stored/reflected
XSS, formula-like spreadsheet cells, path traversal, archive bomb/symlink, secret/log leakage,
unexpected egress, duplicate run/approval, stale candidate, and restore tampering. SSRF/private IP/DNS
rebinding/redirect tests become mandatory before adding a URL connector; no URL capability exists in
the MVP build.
Metric-receipt tampering and missing-member rejection are mandatory for numerical-claim changes.
Malicious editable-agent-prompt, arbitrary agent contract value, version-lineage forgery, and
unresolved workflow-agent binding tests are mandatory for agent-registry or model-gateway changes.
Cloud-model tests must also cover aggregate-scope classification propagation, trust-boundary mismatch,
and HTTPS-only provider allowlisting at the egress proxy.

## Deferred risks

TLS certificate lifecycle/termination is owned by the deployment operator. Real CRM/ERP OAuth,
website crawling, OCR, SSO, external write actions, messaging, voice, and multi-tenant isolation are
outside MVP. Each requires a new threat-model section and ADR before implementation.
