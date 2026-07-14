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

## Change triggers

Re-run evaluation after changes to prompts, output schemas, capabilities, model mapping, retrieval, chunking, canonical mapping, metrics, scoring, source fixtures, or evidence policy. Diagnose data and evidence failures before tuning prompts.

## Failure handling

A failed profile remains configurable for development but cannot be selected as a production-supported profile. Never weaken evidence or unsupported-number gates to make a model pass.
