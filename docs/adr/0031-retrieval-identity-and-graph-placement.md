# ADR-0031: Retrieval Identity and Its Place in the Graph

- **Status:** Proposed — decision required
- **Date:** 28 July 2026
- **Blocks:** SB-10 in `docs/REMEDIATION_ROADMAP.md`

## Context

Two separate problems are tangled together here: what the vector store *is*, and whether
retrieval is part of the workflow at all.

**Identity.** The documents say ChromaDB — `AGENTS.md:36`, `knowledge/AGENTS.md:9,25`,
`IMPLEMENTATION_STATUS.md:20` and the `RagVisualizer` UI badge all name it. There is no
`chromadb` dependency in `pyproject.toml`. What actually runs is `okf/search.py` speaking
HTTP to a `qmd` service (`infra/qmd`, `@tobilu/qmd`), which is behind `profiles: [search]`
and therefore **not started by a default `docker compose up`**. So the default deployment has
no vector retrieval at all — every search silently takes the lexical fallback.

**Placement.** The `knowledge_search` workflow node does not search. It copies
`node.config["query"]` into state and completes (`persistent_runtime.py:283-284`). Retrieval
only happens if an agent calls its `knowledge.search` tool, which routes to
`KnowledgeSearch` (`agents/runtime.py:107-123`). The workflow graph therefore contains a node
that looks like the retrieval step and is not.

A consequence worth noting: `okf/search.py` synthesises locators like `ev_concept_…` for
lexical hits that have no corresponding `EvidenceItem` row, so a locator returned by search
may not resolve through `/api/evidence/{id}`.

## Options

**A. Standardise on `qmd`, correct the documents, move it out of the optional profile.**
Rename every "ChromaDB" reference, make `qmd` part of the default topology so the shipped
system actually has vector retrieval, and keep the lexical fallback as the degraded path.
*Cost:* low. *Consequence:* one more container in the default install.

**B. Adopt ChromaDB for real.** Add the dependency and an embedded or served Chroma instance,
matching what the documents already promise.
*Cost:* medium; adds a heavy dependency (`sentence-transformers` et al.) to an image that is
currently lean. *Consequence:* the documents become true without rewriting them.

**C. Keep `qmd` optional and state plainly that the default deployment is lexical-only.**
*Cost:* none. *Consequence:* honest, but retrieval quality is then not a product property —
it depends on an opt-in profile most installs will never enable.

Independently of A/B/C: **should `knowledge_search` do the retrieval?** Wiring the node to
`KnowledgeSearch` and putting its results into state would make retrieval measurable and
reproducible per run, rather than an opaque side effect of whichever agent happened to call
its tool. The alternative is to delete the node from the catalogue so the editor stops
offering an inert step.

## Recommendation

**A, plus wiring the node.** `qmd` already works and is already integrated with a fallback;
the gap is that it is optional and misnamed. Making it default and correcting the vocabulary
costs almost nothing and removes a class of confusion that has already produced four wrong
statements across the documents.

Wiring `knowledge_search` matters more than it looks: it is the only way retrieval quality
becomes an observable property of a run, which is a precondition for improving it as the
knowledge base grows.

Also fix the synthetic-locator behaviour: a search result should either carry a locator that
resolves to a persisted `EvidenceItem` or carry none, never an `ev_`-prefixed identifier that
cannot be dereferenced.

## Consequences of not deciding

The product claims RAG in its documentation and its UI while the default deployment performs
substring counting, and no run records what was retrieved.
