# Next Steps Guide

The implementation is at release qualification. Do not add a new product module before closing the
remaining release gates.

## Read in this order

1. `IMPLEMENTATION_STATUS.md` — what is actually verified or blocked.
2. `PROJECT_ARCHITECTURE.md` — current implementation and target product architecture.
3. `PRODUCT_DEPLOYMENT_PLAN.md` — customer installation, AWS, inference network, Langfuse, and
   update boundaries.
4. `ENGINEERING_FOCUS_ROADMAP.md` — what to learn before extending the AI/runtime boundary.
5. `EVALUATION_PLAN.md` and `RELEASE_CHECKLIST.md` — acceptance evidence.
6. The relevant ADR and `THREAT_MODEL.md` before changing security, models, OKF, or workflows.

## What to do now

1. Choose exactly one first release candidate: test local `qwen3.5:27b` on suitable hardware or a
   governed Groq/Mistral profile. Keep the installed 9B profile for development: isolated v3 agent
   and deterministic-receipt reviewer calls pass, but full runs failed at Evidence Reviewer and,
   most recently, a Company Analyst retry timeout. The 20-run qualification has not passed on CPU.
   Do not retry native/tool transports
   as a release shortcut without a new, repeatable provider-level fix and golden evidence.
2. Run the setup structured-output probe. Do not enable automatic provider fallback.
3. Run `scripts/qualify-model.ps1` (or `.sh`) with 20 attempts. A failed profile is not “supported.”
4. Complete the browser journey from a clean installation through approved report and OKF export.
   Use `browser-real-model-e2e.ps1`/`.sh`; it intentionally refuses auth bypass and requires an
   explicit disposable-install confirmation.
5. Restart once during a run and once during approval; confirm the same DBOS/run ID resumes.
6. Run qmd loss/rebuild, no-egress, release scan, backup, restore, and exact-citation checks.
7. Run `scripts/release-rehearsal.sh` on a separate clean Linux x86-64 host behind HTTPS. Accept the
   gate only when its content-safe manifest reports every step passed.

## Rules while fixing failures

- Check mappings, immutable evidence, and deterministic metrics before editing prompts.
- Run evaluation after changing prompts, schemas, tools, retrieval, mappings, scoring, or model IDs.
- Never call an LLM score probability/confidence and never weaken the evidence gate to pass eval.
- Preserve unknown OKF types/metadata and keep OKF/PostgreSQL ownership separate.
- Keep connectors read-only; do not add a write method “for later.”
- Add a new ADR for a boundary-changing decision and update status in the same change.
- Do not copy provider keys, prompts, source text, or evidence excerpts into logs or tickets.
- Treat Langfuse as a content-safe observability sink. Verify retention, access control, self-hosted
  telemetry, and licensing before enabling it for a customer.
- Keep the deterministic four-agent Growth Diagnostic as the supported MVP workflow. Do not replace
  it with a dynamic worker loop before bounded-task evaluation and recovery gates pass.
- A customer may configure safe workflow drafts, but new connectors, capabilities, MCP bridges, or
  writes are vendor-delivered changes with a new ADR and security review.

## When a real company arrives

- Classify its data and confirm retention, privacy, consent, and legal requirements.
- Discover the actual CRM/ERP before choosing the first connector.
- Benchmark the approved local hardware and model profile with representative permitted data.
- Update mappings, threat model, backup policy, golden fixtures, and evidence expectations.
- Start with a read-only pilot and human comparison. Controlled writes require a separate ADR,
  capability, approval, consent, rollback, and security review.

## When the product is deployed

- Record the customer deployment profile: local private, managed AWS private, customer AWS private,
  or split private.
- Record who owns the AWS account/VPC, TLS, backups, updates, rollback, model runtime, and
  observability retention.
- Never expose Ollama/vLLM publicly. Use the approved same-VPC, private-VPN, or outbound-inference
  gateway pattern.
- Test one customer update from backup through migration, smoke test, and rollback before promising
  a release.
