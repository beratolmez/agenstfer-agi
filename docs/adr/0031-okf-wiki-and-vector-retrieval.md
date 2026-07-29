# ADR-0031: OKF Wiki and Vector Retrieval as One Retrieval Layer

- **Status:** Accepted
- **Date:** 29 July 2026
- **Supersedes:** the draft that framed this as a choice between qmd and ChromaDB
- **Drives:** SB-10 in `docs/REMEDIATION_ROADMAP.md`
- **Relates to:** ADR-0001 (OKF / PostgreSQL ownership), ADR-0007 (approval-controlled
  candidate lifecycle)

## Context

The earlier draft asked the wrong question. It offered a choice — standardise on qmd, adopt
ChromaDB, or accept lexical-only — as if the wiki and the vector index were alternatives.
They are not. They answer different questions and the product needs both.

What is actually true today:

- The **OKF Wiki** (Git-backed Markdown under `knowledge/bundles/company/`) is the source of
  truth. It is structured, versioned, approval-gated, and every concept resolves to a
  persisted evidence locator. This part works.
- **Vector retrieval** exists as `okf/search.py` speaking HTTP to a `qmd` service, with a
  lexical fallback. It sits behind `profiles: [search]`, so **a default `docker compose up`
  has no vector retrieval at all** — every search silently degrades to substring counting.
- The documents name ChromaDB in four places (`AGENTS.md:36`, `knowledge/AGENTS.md:9,25`,
  the `RagVisualizer` badge) while `pyproject.toml` declares no such dependency.
- The `knowledge_search` workflow node does not search. It copies `node.config["query"]`
  into state and completes (`persistent_runtime.py:283-284`). Retrieval only happens if an
  agent calls its `knowledge.search` tool.
- Lexical hits synthesise locators like `ev_concept_…` (`okf/search.py:74`) that have no
  corresponding `EvidenceItem`, so a citation returned by search may not resolve through
  `/api/evidence/{id}`. For a product whose core promise is evidence custody, that is a
  correctness defect, not a cosmetic one.

## Decision

Retrieval is **one layer with two complementary paths over the same active OKF bundle.**

**1. The OKF Wiki remains the source of truth; the vector index is derived and disposable.**
Unchanged from ADR-0001 and AGENTS.md, and now stated as an invariant: the index can be
deleted and rebuilt from the active bundle at any time without data loss. Candidate bundles
are never indexed — only the approved active revision is.

**2. Two retrieval paths, chosen by the shape of the question.**

| Path | Answers | Properties |
|---|---|---|
| **Structural / lexical** over the wiki | "give me this concept", "which references cite this source", exact term match | Deterministic, reproducible, cheap |
| **Vector** over the derived index | "what do we know about X" when the concept path is unknown | Semantic recall, approximate |

**3. Hybrid by default.** A retrieval request runs both paths, merges by concept path,
deduplicates and ranks. Neither path alone is the product: the wiki alone misses
paraphrase, the vector index alone cannot guarantee the structural and citation
guarantees the evidence gate depends on.

**4. Locators come from the wiki and the evidence store, never from the index.** The vector
index stores concept paths and returns them; the locator is resolved from the OKF concept
and its persisted `EvidenceItem`. A result that cannot be resolved to a real evidence id
carries **no locator at all** rather than a synthesised one. This closes the
`ev_concept_…` defect and keeps every citation dereferenceable.

**5. The vector service is part of the default topology.** Moving it out of
`profiles: [search]` is what makes "hybrid" true in a shipped install rather than in a
document. The lexical path remains the degraded mode when the service is unreachable, and
the run records which mode served each retrieval so quality is measurable.

**6. Retrieval belongs in the workflow graph.** `knowledge_search` performs the retrieval and
writes its results — query, mode, concept paths, resolved locators — into run state. Today
retrieval is an opaque side effect of whichever agent happened to call a tool; after this it
is a reproducible, auditable step of the run.

**7. The vector backend is an implementation detail behind a seam.** `okf/search.py` is that
seam. `qmd` is the shipped adapter. Architecture documents describe the *capability*
("vector retrieval over the active OKF bundle"), not a product name — which is what let
"ChromaDB" drift into four documents while nothing imported it. Swapping to Chroma, pgvector
or anything else must be an adapter change, not an architecture change.

**8. Reindex is bound to approval.** The index is rebuilt when a candidate merges into the
active bundle, because that is the only moment the source of truth changes.

## Consequences

- The default install gains a container. That is the honest cost of shipping a system whose
  documentation and UI both claim RAG.
- Citations become dereferenceable in every path. Some results will carry no locator, which
  is correct and more useful than an id that 404s.
- Retrieval quality becomes an observable property of a run, which is the precondition for
  improving it as the knowledge base grows beyond the demo dataset.
- The four "ChromaDB" references must be corrected to describe the capability. `qmd` remains
  named only where the concrete adapter is being discussed.
- Two paths mean two failure modes. The run must always record which one served the result;
  a silent degrade to lexical is what hid this problem in the first place.

## Verification

- With the vector service stopped, retrieval still returns results and the run records the
  degraded mode.
- Every locator returned by retrieval either resolves through `/api/evidence/{id}` or is
  absent; no synthesised `ev_…` identifier is ever emitted.
- A `knowledge_search` node writes its query, mode and resolved concept paths into run state,
  visible in `GET /api/runs/{id}`.
- Approving a candidate triggers a reindex; a query for content added by that candidate
  returns it afterwards and did not before.
