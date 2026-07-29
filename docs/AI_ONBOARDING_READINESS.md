# AI Onboarding Readiness

Assessed 29 July 2026 against the question: **can an AI coding agent that has never seen
this project pick it up from the repository alone and do useful work?**

Overall: **ready for packaged work, unproven for open-ended work.** Of the eleven gaps found,
nine were closed while writing this. The tenth — the absence of CI, the highest-leverage item
— now has a workflow committed, but it has never executed: GitHub Actions refuses to start
any job on this account because of a billing lock. Three gaps therefore remain open, named
below.

This is a point-in-time assessment. Re-run it when the repository structure changes
materially; it is not a living document.

---

## How this was judged

The criteria below are not opinions about document quality. Each was turned into a question a
new agent would actually have to answer on its first day, and the repository was checked for
whether it answers it:

1. **Cold-start questions.** Twelve questions any agent must answer before writing code
   ("what is this", "what works today", "what should I work on", "how do I run it", "when am
   I done", "why is X like this", "where do I put what I learn"). Each was traced to a
   specific file and section, or recorded as unanswered.
2. **Reference integrity.** Every ADR citation, cross-document link and code path referenced
   in the entry documents was checked for resolution. This found the `ADR-004` / `ADR-0004`
   collision, since fixed.
3. **Claim-versus-code sampling.** Figures and version numbers in the living documents were
   compared against the code they describe. This found the stale `company-analyst` row in
   `CAPACITY_AND_QUOTA.md` and the understated corpus size in the guide, both since fixed.
4. **Chat-dependency sweep.** Everything learned in the session that produced this document
   was checked against the repository: is it written down, or would it have to be
   rediscovered? Two items were only in conversation and were moved into the repository.

**What was *not* done, and why it matters:** no fresh agent was actually run against these
documents. The decisive test of onboarding is whether a cold agent gets stuck, and that test
has not been executed. Every verdict below is therefore an assessment of whether the
information *exists and resolves*, not proof that it *lands*.

---

## Criterion 1 — Can a new AI agent understand the project without chat history?

**Verdict: ready, with one hole.**

Eleven of the twelve cold-start questions resolve to a specific document and section:

| Question | Answered by |
|---|---|
| What is this product? | `AI_DEVELOPMENT_GUIDE.md` §2 |
| What actually works today? | `IMPLEMENTATION_STATUS.md`, top section |
| What is only specified? | Same document, gap entries |
| What should I work on next? | `REMEDIATION_ROADMAP.md` |
| What must I read for *my* task? | Guide §3, thirteen task types |
| What may I skip? | Guide §3, "on demand" and "historical" |
| How do I run and verify it? | Guide §6, `OPERATIONS_RUNBOOK.md` |
| When may I say "done"? | Guide §5 |
| Why is X the way it is? | `adr/README.md` → the ADR |
| What must I not do? | `AGENTS.md` product boundaries |
| Where do I put what I learn? | Guide §7 |
| What traps have cost time before? | Guide §11 |

**The hole: workflow authoring.** The guide's workflow row points at `validator.py` and
`default.py` — the rules and the reference implementation — but no document explains how a
user authors a workflow through the UI, and that path has never been driven end-to-end in a
browser. `IMPLEMENTATION_STATUS.md` records the consequence (a user-authored workflow routes
to the fallback engine, not the LangGraph one) but not the authoring experience itself. An
agent asked to fix a workflow-builder defect would be working blind.

*To close:* drive the authoring path in a browser the way the demo path was driven, then
write `docs/WORKFLOW_AUTHORING.md`. Half a day, and it will surface defects — the same
exercise on the demo path found six.

---

## Criterion 2 — Are architecture decisions findable in one place?

**Verdict: ready.**

`docs/adr/` is the single location and now carries its own index (`adr/README.md`)
distinguishing the twelve load-bearing ADRs from the ten that are change logs rather than
decisions. Three defects found during this assessment are fixed:

- `ADR-004` (onboarding) collided with `ADR-0004` (no external write in MVP). An agent told
  to check ADR-0004 before adding an outbound capability could have landed on the wrong
  document and concluded the boundary did not exist. Renumbered to 0034.
- Opening `docs/adr/` directly gave 34 filenames with no relevance signal. The index fixes
  this.
- Several audit-round ADRs claim resolution that the following audit disproved. The index now
  states that `IMPLEMENTATION_STATUS.md` outranks an ADR's self-assessment.

**Residual, accepted:** ADR-0002 and ADR-0011 are gutted to the single word `DELETED` with no
superseding pointer. Their subjects are covered by ADR-0016 and ADR-0029, and both the guide
and the ADR index say so, so a reader is not misled. Reconstructing them is not worth the
effort; the mitigation is the note.

---

## Criterion 3 — Are development standards clear enough?

**Verdict: clear as documentation. Enforcement is configured but not yet running.**

The standards exist and are specific: `AGENTS.md` for boundaries and the handoff protocol,
guide §5 for the definition of done, §8 for task packaging, §9 for conventions. §5 is
deliberately behavioural rather than procedural — it requires that you ran the thing, that a
regression test fails against the broken code, that numbers are measured rather than
estimated, and that you say explicitly what you could not verify.

**This was the largest gap in the original assessment. It is addressed but not closed.**
`.github/workflows/ci.yml` is committed and runs lint, the backend suite, migration drift,
frontend tests, the TypeScript build and all six Compose overlays on every push and pull
request.

**It has never run.** On its first trigger GitHub refused all three jobs before they started:
*"The job was not started because your account is locked due to a billing issue."* Actions
parsed the workflow and created the three jobs with the correct names, so the file is valid,
and every command in it was executed locally first — `uv sync --locked`, `npm ci`, the full
`project-check.sh` at exit 0, and the guard against five cases. But a pipeline that cannot
start enforces nothing.

*To close:* resolve GitHub Actions billing on the account, push, and confirm a green run.
Until then requirement 2 of the definition of done remains a claim by the author of the
change, exactly as before — the difference is that the mechanism is now waiting rather than
missing.

Closing it surfaced a defect that explains a lot: **both `project-check` scripts failed on a
clean checkout.** The plaintext-key guard matched the *variable* rather than a *value*, so the
correct secret-free state — `AGI_CLOUD_API_KEY: ""` — tripped it. A gate that fails on an
untouched tree teaches people to stop running it, which is roughly how this repository arrived
at honour-system quality control. Fixed in both shells and verified against five cases.

**What CI still cannot check** is requirements 1, 3, 4, 5 and 6: whether you ran the thing,
whether your regression test would fail against the broken code, whether a real provider was
called, whether you loaded the page, whether a number was measured. Those remain honour-system
by nature, and they are where every model-layer and UI defect in this project's history hid.
The guide now says this explicitly rather than letting a green badge imply more than it means.

*Interim:* `scripts/project-check.sh` / `.ps1` is the same set of checks and now passes on a
clean tree. It is skippable, which is the whole problem, but it is what exists today.

---

## Criterion 4 — Is task-based onboarding sufficient?

**Verdict: structurally complete, empirically unproven.**

Thirteen task types have reading rows; seven have starting prompt templates; the task packet
format (goal / files / change / out of scope / verification / done when) is specified in
guide §8 and the roadmap points at it.

**But no packet has ever round-tripped.** The format is a hypothesis about what a different
agent needs, written by an agent that already had full context. The specific risk is
mis-sizing: a packet that reads as complete to its author may leave a cheaper model without
enough to act, or — worse — with enough to act confidently and wrongly.

*To close:* package roadmap items T6 (remove dead `mcp.*` capabilities) and T11
(`knowledge_search` records what it retrieved) as the first two packets, run them through the
intended executing agent, and check the packets into the repository as worked examples. Both
are small and self-contained, so a failure is cheap and diagnostic. Half a day, and it
converts §8 from a proposal into a demonstrated format.

---

## Criterion 5 — Is there unnecessary or duplicated documentation?

**Verdict: reduced, not eliminated. Acceptable.**

Of 7,952 documentation lines, 2,204 are historical: `AUDIT_FINDINGS.md` (987),
`AUDIT_RAPORT.md` (603), `ARCHITECTURE_ASSESSMENT.md` (254), `archive/` (360). All are now
fenced — banners on the files, a "do not read for context" row in the guide, a closed section
in `docs/README.md`.

They are fenced rather than deleted deliberately. They are the traceability record for how
the current roadmap was derived, and the cost of keeping them is zero once agents are told
not to read them. Deleting them would destroy the audit trail to save context that is already
not being spent.

**Residual overlap, judged not worth fixing:**

- `PROJECT_ARCHITECTURE.md` (39 lines) and `SYSTEM_ARCHITECTURE.md` (126) have names that do
  not distinguish them. `docs/README.md` disambiguates by the question each answers, which is
  the mitigation that matters — but the filenames still invite a wrong open.
- ADRs 0019–0025 are seven consecutive "audit round N fixes" documents. They dilute the ADR
  folder, which is why `adr/README.md` now segregates them.

Neither misleads a reader who follows the entry documents. Renaming would break inbound links
for cosmetic benefit.

---

## Criterion 6 — Is any knowledge still dependent on chat history?

**Verdict: everything identified has been moved. I cannot certify none remains.**

Two items existed only in conversation and are now in the repository:

- **Routing Gemini through OpenRouter re-introduces the `thought_signature` failure.** Only
  the direct Gemini provider uses the native transport; an aggregator falls back to the
  OpenAI shim and fails on the first parallel tool call — the exact defect ADR-0026 fixed.
  Anyone moving to OpenRouter for cheaper multi-model testing would hit this with no way to
  diagnose it. Now in `CAPACITY_AND_QUOTA.md` with the measurement behind it.
- **The UI's characteristic failure mode.** Four of the six defects found when the console was
  first driven in a browser shared one shape: the interface hid what was required and
  swallowed what went wrong. That pattern is worth more than the individual bugs. Now a
  standing question in guide §11.

**The limit of this claim:** a sweep for chat-dependent knowledge is performed by the agent
that holds the chat, which is the least reliable auditor of what it knows implicitly. The
honest position is that the known unknowns are closed and the unknown unknowns are exactly
what a cold-start test would reveal — see the method note above.

Deliberately not in the repository: provider API keys, and the demo credentials beyond what
`DEMO_SCRIPT.md` needs. That is correct, not a gap.

---

## Criterion 7 — Is the repository mature enough to be continued by different AI agents?

**Verdict: yes for packaged work, not yet for open-ended work.**

**Ready now:** a bounded task delivered as a packet — one roadmap row, named files, a stated
verification command, an explicit out-of-scope list. The entry path, the reading map, the
definition of done and the decision record all support this, and the traps most likely to
burn a session are written down.

**Not ready:** handing an agent an open-ended goal ("improve retrieval", "make the workflow
builder work") and expecting a sound result. Three things block it:

1. CI is configured but blocked at the account level, so "the tests pass" is still the
   author's word (criterion 3). This one is not engineering work — it is a billing setting.
2. The packet format has not been validated against the model that will execute it
   (criterion 4).
3. One significant path — workflow authoring — is undocumented and unverified (criterion 1).

The order matters: until CI runs, a packet that comes back green from a cheaper model has to
be taken on trust, which makes the second item hard to evaluate honestly.

---

## What is not ready — the short list

| # | Gap | Effort | Why it matters |
|---|---|---|---|
| 1 | **CI cannot start** — account locked for Actions billing | billing, not engineering | The workflow is written and locally verified; nothing enforces it until a run completes |
| 2 | **Task packet format unproven** — no packet has round-tripped through the executing agent | ~4 h | The delegation model rests on it; T6 and T11 are the cheap tests |
| 3 | **Workflow authoring undocumented and unverified** in a browser | ~4 h | The one significant path an agent cannot learn from the repository |

Everything else found in this assessment has been fixed: the ADR number collision, the
missing ADR folder index, the stale capacity figure, the understated corpus size, the two
pieces of chat-only knowledge, and the broken secret guard that writing the CI workflow
exposed — both `project-check` scripts had been failing on a clean checkout.

---

## What would change the verdict to "ready"

Close the three items above — the first is a billing setting, not a day of work — then
re-run this assessment the only way that proves anything:
give a fresh agent a packet and the repository, no conversation, and see where it stops. What
it asks for is the real gap list. Everything in this document is a prediction of that result.
