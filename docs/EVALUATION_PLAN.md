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

## Change triggers

Re-run evaluation after changes to prompts, output schemas, capabilities, model mapping, retrieval, chunking, canonical mapping, metrics, scoring, source fixtures, or evidence policy. Diagnose data and evidence failures before tuning prompts.

## Failure handling

A failed profile remains configurable for development but cannot be selected as a production-supported profile. Never weaken evidence or unsupported-number gates to make a model pass.

