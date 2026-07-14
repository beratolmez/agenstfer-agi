# Next Steps Guide

The implementation is at release qualification. Do not add a new product module before closing the
remaining release gates.

## Read in this order

1. `IMPLEMENTATION_STATUS.md` — what is actually verified or blocked.
2. `PROJECT_ARCHITECTURE.md` — boundaries and ownership.
3. `EVALUATION_PLAN.md` and `RELEASE_CHECKLIST.md` — acceptance evidence.
4. The relevant ADR and `THREAT_MODEL.md` before changing security, models, OKF, or workflows.

## What to do now

1. Choose exactly one first release candidate: test local `qwen3.5:27b` on suitable hardware or a
   governed Groq/Mistral profile. Keep the installed 9B profile for development: its v3 Growth
   Opportunity node now passes, but the full run and 20-run qualification have not passed on CPU.
2. Run the setup structured-output probe. Do not enable automatic provider fallback.
3. Run `scripts/qualify-model.ps1` (or `.sh`) with 20 attempts. A failed profile is not “supported.”
4. Complete the browser journey from a clean installation through approved report and OKF export.
5. Restart once during a run and once during approval; confirm the same DBOS/run ID resumes.
6. Run qmd loss/rebuild, no-egress, release scan, backup, restore, and exact-citation checks.
7. Repeat the release rehearsal on a clean Linux x86-64 host behind HTTPS.

## Rules while fixing failures

- Check mappings, immutable evidence, and deterministic metrics before editing prompts.
- Run evaluation after changing prompts, schemas, tools, retrieval, mappings, scoring, or model IDs.
- Never call an LLM score probability/confidence and never weaken the evidence gate to pass eval.
- Preserve unknown OKF types/metadata and keep OKF/PostgreSQL ownership separate.
- Keep connectors read-only; do not add a write method “for later.”
- Add a new ADR for a boundary-changing decision and update status in the same change.
- Do not copy provider keys, prompts, source text, or evidence excerpts into logs or tickets.

## When a real company arrives

- Classify its data and confirm retention, privacy, consent, and legal requirements.
- Discover the actual CRM/ERP before choosing the first connector.
- Benchmark the approved local hardware and model profile with representative permitted data.
- Update mappings, threat model, backup policy, golden fixtures, and evidence expectations.
- Start with a read-only pilot and human comparison. Controlled writes require a separate ADR,
  capability, approval, consent, rollback, and security review.
