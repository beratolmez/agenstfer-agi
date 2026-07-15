# Evaluation Plan

## Golden dataset

Use the deterministic Anka dataset through the same connector and mapping path used by uploaded files. Keep six planted opportunity/data-quality cases and expected evidence locators in versioned fixtures. Do not expose expected answers to agent prompts.

## Release metrics

- Detect at least five of six planted cases.
- Resolve evidence for 100% of material claims.
- Produce zero unsupported numerical claims.
- Achieve at least 95% typed structured-output success across the evaluation suite.
- Achieve at least 70% top-five overlap across repeated runs with fixed inputs and profile.
- Keep scoring reproducible independent of model wording.

## Profile qualification

Every release-enabled local or cloud model profile runs the same suite. Record provider, exact model ID, prompt/agent versions, retrieval revision, date, hardware where local, latency, token usage, pass/fail, and failure samples. The setup wizard may call a profile “supported” only after a qualifying result exists for the released version.

The executable harness must clone and publish the current built-in workflow, pin the selected model
profile and exact agent versions, and execute it through the same persistent workflow runtime used by
production. A legacy synchronous diagnostic is not qualification evidence. The content-safe report
records workflow identity, per-attempt retrieval revisions, agent bindings, the control-plane policy
revision, and SHA-256 hashes of the effective prompts; it never records prompt text.

The harness records content-safe per-attempt duration, total token usage, material/supported claim
counts, unsupported numerical-claim count, safe failure class/stage, CPU/memory, and available Ollama
context/runtime metadata. It never records prompts, model response bodies, or evidence excerpts.

Run the executable qualification harness only after configuring the selected provider:

```powershell
.\scripts\qualify-model.ps1 -Profile local-balanced -Attempts 20
```

For a governed cloud profile use `-Profile cloud-balanced`. The JSON result is written under
`artifacts/release/` and contains only safe error classes—not prompts, source text, or secrets.

Linux uses `./scripts/qualify-model.sh <profile> <attempts>`. The wrapper executes inside the
isolated app network and copies the safe JSON report to `artifacts/release/`.

Observed on 14 July 2026: installed `qwen3.5:9b` passed the real structured-output probe. Its first
bounded full run completed Company Analyst but Growth Opportunity Analyst exhausted the 360-second
retry budget; the run failed closed after 622 seconds. This is diagnostic evidence, not a release
qualification, and the profile remains unsupported.

The audit found a v2 prompt/contract contradiction: the prompt allowed up to ten hypotheses while
the typed contract requires exactly five unique deterministic signal IDs. Growth Opportunity Analyst
v3 removes that contradiction, requires one short rationale per supplied signal, and uses a 900-token
output budget. A real isolated v3 node call returned all five required IDs in one request in 278.29
seconds. This validates the contract correction only; it does not replace a complete diagnostic or
the 20-run profile qualification.

Observed on 15 July 2026: Company Analyst v3 passed an isolated real call in 171.5 seconds, and a
five-claim Evidence Reviewer batch backed by deterministic metric receipts returned exact `5/5`
supported decisions in 165.78 seconds. These component passes were not repeatable end to end. One
full attempt failed at Evidence Reviewer with `UnexpectedModelBehavior` after 939.27 seconds. The
latest telemetry-enabled attempt failed at Company Analyst after 307.53 seconds when its retry
exhausted the timeout; it recorded 12 CPUs, 7,902 MiB memory, 8,192 context, and no VRAM. Native JSON
Schema returned `json_invalid`; ToolOutput was not repeatable and Ollama returned malformed
function-call XML with HTTP 500. PromptedOutput remains configured and 9B remains unsupported.

## Change triggers

Re-run evaluation after changes to prompts, output schemas, capabilities, model mapping, retrieval, chunking, canonical mapping, metrics, scoring, source fixtures, or evidence policy. Diagnose data and evidence failures before tuning prompts.

ADR-0008 changed the effective prompt by adding a mandatory control-plane system policy. Therefore
all component observations recorded above are diagnostic history only for the earlier effective
prompt. The next qualification must record the current agent versions and effective-policy revision;
no earlier isolated pass can qualify the current build.

Observed on 15 July 2026 with the current production-path harness and policy revision
`2026-07-15.1`: one `local-balanced` smoke attempt pinned workflow
`qualification-local-balanced:1` and agent versions `3/3/3/2`, then failed closed at
`company_agent` with `TimeoutError` after 313.34 seconds. The container reported 12 CPUs, 7,902 MiB
memory, 8,192 Ollama context, and no VRAM. This validates harness provenance and failure recording;
it is not qualification, and 9B remains unsupported.

## Failure handling

A failed profile remains configurable for development but cannot be selected as a production-supported profile. Never weaken evidence or unsupported-number gates to make a model pass.
