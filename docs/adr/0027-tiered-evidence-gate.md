# ADR-0027: Tiered Evidence Gate — Deterministic Claims Block, Narrative Claims Are Withheld

- **Status:** Accepted
- **Date:** 28 July 2026
- **Relates to:** ADR-0026 (made the gate reachable), PRD §4.5 (Evidence Based AI), §6.2 (Evidence
  and Provenance), AGENTS.md ("Every material or numerical generated claim must resolve to
  persisted evidence and an immutable source locator").

## Context

With the model-gateway defects fixed (ADR-0026) the diagnostic reached the evidence gate, which
then failed every run. `_enforce_evidence_gate` treated all material claims identically:

```python
if failures or not review.approved:
    raise ValueError(...)
```

Material claims come from two very different producers:

- **Deterministic claims** (`metric-*`) are computed by `domain/metrics.py` and carry a
  verification receipt (`signal.verification_evidence_id`) whose hash is checked against the
  immutable snapshot. If one of these is unsupported, the computation itself is untrustworthy.
- **Narrative claims** — company strengths/weaknesses and `hypothesis-*` rationales — are written
  by a model. They are prose, and a reviewer model judges whether the cited excerpts support them.

Against the demo dataset the reviewer consistently rejected narrative claims: the excerpts are
order and account records, while the rationales assert market feasibility and service demand.
Tightening the analyst prompts (ADR-0026) reduced but did not eliminate this. Under an
all-or-nothing gate the product could never produce a first diagnostic, which defeats its purpose.

The PRD's evidence contract says an unevidenced claim must not be *published as evidence-backed*
and that missing data must be surfaced (§6.2 "eksik veri uyarıları", "alternatif yorumlar"). It
does not say that an unevidenced sentence must suppress an otherwise evidence-backed report.

## Decision

The gate is tiered.

1. **Deterministic `metric-*` claims are blocking.** A rejected, missing or evidence-less
   deterministic claim raises and fails the run. Numbers never ship unverified.
2. **Narrative claims are withheld, not fatal.** A rejected narrative claim is excluded from the
   published report and recorded as a data gap carrying the reviewer's own reason. The
   corresponding opportunity keeps its deterministic signal, score and evidence references; only
   the unsupported rationale is replaced with `UNVERIFIED_RATIONALE`, which states plainly that the
   model's reasoning could not be verified.
3. **Reviewer contradictions become data gaps.** `review.contradictions` is surfaced to the reader
   instead of being discarded.
4. **`review.approved` alone is no longer fatal.** The reviewer sets it to `False` whenever any
   claim is unsupported, which under this policy is an expected, reportable outcome. Only
   deterministic failures stop the run.

`_enforce_evidence_gate` returns an `EvidenceGateResult` (`evidence_ids`, `rejected_claim_ids`,
`data_gaps`) instead of a bare ID list, and both diagnostic pipelines pass it into
`build_computed_diagnostic`.

## Consequences

- The first diagnostic completes end-to-end: 12 nodes, human approval, OKF candidate merged.
  Verified live against Gemini — 5 deterministic opportunities published with 2–3 resolved
  evidence references each, 14 withheld-claim and contradiction gaps reported.
- The evidence guarantee is **stronger**, not weaker, for what reaches the reader: previously a
  reviewer's reasons were thrown away with the exception; now every rejection is attributed and
  visible in the report.
- A reader can distinguish "no rationale was verifiable" from "there is no opportunity", because
  the deterministic score and evidence remain attached.
- Risk: a report whose rationales are largely withheld looks thin. That is the honest signal —
  it means the connected sources do not yet support narrative analysis, and the data gaps say so.
- The demo dataset remains the weak link. Richer, better-linked source data is what turns withheld
  rationales into published ones; that is data work, not gate work.

## Verification

- `test_deterministic_claim_rejection_fails_without_creating_candidate` — a rejected `metric-*`
  claim fails the run and creates no OKF candidate.
- `test_narrative_claim_rejection_is_withheld_not_fatal` — a rejected `hypothesis-*` claim leaves
  the run completing, replaces only that rationale, keeps the signal's evidence, and reports the
  claim id as a data gap.
- Live run: `status: completed` after approval, with `evidence_ids` populated and every rejection
  attributed in `data_gaps`.
