# Task packet — T10: retrieval must never emit a locator it cannot resolve

Packet format: [`AI_DEVELOPMENT_GUIDE.md`](../AI_DEVELOPMENT_GUIDE.md) §8. Read the floor
(guide §1) before starting. Task type: **bug fix, backend only** — guide §3 says read the
reproduction first, then only the module involved.

This is a correctness defect in the evidence chain, which guide §2 calls the product itself:
a citation that cannot be dereferenced undermines the one claim the system makes.

ADR-0031 §4 already decided the rule — a result "carries **no locator at all** rather than a
synthesised one". The code implements it in one branch and not the other.

---

```
Goal          : A retrieval result never carries a locator that has no EvidenceItem
                behind it. Where resolution is impossible, the locator is None.

Files         : apps/api/agi_server/okf/search.py:36-48   (_resolve_locator)
                apps/api/agi_server/main.py:1826-1834      (knowledge_list)
                apps/api/tests/test_knowledge_retrieval.py:93-103

Change        : (a) _resolve_locator already resolves correctly when it has a session:
                    it looks the id up in EvidenceItem and returns None on a miss. When
                    self.db is None it instead returns raw_loc unchecked -- an
                    unverifiable locator straight from the vector service. Make that
                    branch return None. Resolution is impossible without a session, and
                    ADR-0031 says the answer to "impossible" is no locator.

                (b) GET /api/knowledge?query=... constructs
                    KnowledgeSearch(bundle, settings.qmd_url) with no session, which is
                    why the defect is reachable in production. Give knowledge_list a
                    db dependency -- `db: Annotated[Session, Depends(get_db)]`, the same
                    shape every other endpoint in main.py uses -- and pass db= through.
                    agents/runtime.py:116 already passes it and needs no change.

                (c) test_knowledge_search_maps_chroma_hits asserts
                    `hit.locator == "ev_concept_pricing.md"` while constructing
                    KnowledgeSearch without a session. That test encodes the defect as
                    the contract. Rewrite it to assert the locator is None, and add a
                    case with a session where the EvidenceItem exists, proving a
                    resolvable locator still survives. Do not weaken the fix to keep the
                    old assertion green.

Out of scope  : Do NOT implement T11 (recording query, mode and resolved locators into
                run state). It is the next packet and shares these files.
                Do NOT change the qmd adapter, the lexical fallback, or the search
                ranking. Only locator resolution.
                Do NOT touch agents/runtime.py -- it is already correct.
                Do NOT change SearchHit's shape; locator is already `str | None`.

                Environment: do not modify passwords, database rows, containers or
                configuration. This packet needs no running stack. If something blocks
                you, stop and report it rather than changing the machine.

Verification  : uv run python -c "
                import sys; sys.path.insert(0,'apps/api')
                from agi_server.okf.search import KnowledgeSearch
                from agi_server.okf.bundle import FileSystemOKFBundle
                from agi_server.config import Settings
                s = KnowledgeSearch(bundle=FileSystemOKFBundle(Settings().company_bundle),
                                    qmd_url=None)
                print('raw, no session ->', repr(s._resolve_locator('ev_concept_pricing.md',
                                                                    'pricing.md')))"

                Today prints:      raw, no session -> 'ev_concept_pricing.md'
                After the fix:     raw, no session -> None

                Then the whole gate:
                ./scripts/project-check.sh          # or scripts\project-check.ps1
                Expected: exit 0.

Done when     : 1. The command above prints None, and you have pasted both the before
                   and the after output. Run it before you change anything -- an
                   after-only result does not show the behaviour changed.
                2. The rewritten test fails against the unfixed search.py and passes
                   against the fixed one. State that you ran it both ways.
                3. GET /api/knowledge?query=... passes a session, verified by reading
                   the call site, and the full gate is exit 0.
                Exactly one existing test fails when the fix is applied --
                test_knowledge_search_maps_chroma_hits. If any other test fails, stop:
                something outside this packet's scope has changed.
```

---

## Facts already established — do not re-derive

Measured on this codebase before the packet was written:

- `_resolve_locator(None, "pricing.md")` with no session already returns `None`. Only the
  `raw_loc` branch is wrong.
- `_resolve_locator("ev_concept_pricing.md", "pricing.md")` with no session returns the string
  unchanged. That is the whole defect.
- `KnowledgeSearch` has exactly two production call sites: `agents/runtime.py:116` (passes
  `db`, correct) and `main.py:1833` (does not).
- Applying the fail-closed change breaks exactly one test, named above. Nothing else in the
  suite depends on the unresolved passthrough.
- `ev_concept_…` is not synthesised by our code. It arrives in the vector service's response
  and is passed through, which is why the fix belongs at the resolution boundary rather than
  wherever such strings are built.

## Why fail closed rather than only fixing the caller

Fixing `main.py` alone would close today's reachable path and leave the trap for the next
caller who forgets the session argument. The resolution function is the boundary where the
guarantee belongs, so it should be impossible to obtain an unresolved locator from it. Both
changes are in scope precisely because either alone is insufficient — one fixes the instance,
the other fixes the class.

## Reporting back

State what the verification command printed before and after, whether the rewritten test was
run against both versions of `search.py`, and the exit code of the gate. If you could not run
something, say which and why — guide §5: an honest "I could not test this" is worth more than
a confident claim that turns out to be wrong.
