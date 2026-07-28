# Growth Context Graph — Current State and Target Mapping

**Status:** Generic infrastructure exists; the entity model is a fraction of the target.
**Source requirement:** PRD §6.1, named in PRD §19 as the first of the four core components.

---

## What exists

The graph infrastructure is real and reusable. Two tables carry it:

**`CanonicalEntity`** (`db.py:138-163`) — a source-neutral business entity with external keys
and classified attributes.

**`CanonicalFact`** — a typed subject / predicate / object relation carrying `evidence_ids`
and optional validity time.

This is a genuine property graph with evidence binding on every edge, which is the part that
matters most and the part hardest to retrofit. It is not the limitation.

The limitation is what gets *written* into it. Entities come from exactly one synthetic
connector (`connectors/demo.py:6-13`), producing seven types:

`accounts` · `contacts` · `opportunities` · `activities` · `products` · `orders_invoices` ·
`strategy_documents`

---

## Target versus actual

PRD §6.1 lists 25 entity types. Mapping them:

| PRD entity | Status |
|---|---|
| Company | Installation-level, in `InstallationState.configuration` rather than the graph |
| Account | ✅ `accounts` |
| Contact | ✅ `contacts` (only `role`, `email` — `domain/demo.py:48-55`) |
| Opportunity | ✅ `opportunities` |
| Product | ✅ `products` |
| Invoice / Order | ✅ `orders_invoices` (combined) |
| Data Source | ✅ `DataSource` table (outside the graph) |
| Evidence Item | ✅ `EvidenceItem` table (outside the graph) |
| Lead | ❌ — claimed in `IMPLEMENTATION_STATUS.md:13`, never produced |
| Customer | ❌ (not distinguished from Account) |
| Service | ❌ |
| Campaign | ❌ |
| Channel | ❌ |
| Competitor | ❌ |
| Event | ❌ |
| Conversation / Call / Email / Social Interaction | ❌ |
| Proposal | ❌ |
| Consent Record | ❌ (see `CONSENT_LEDGER.md`) |
| Recommendation | ⚠️ produced as run output (`GrowthDiagnostic.opportunities`), not persisted as a graph entity |
| Agent Action | ⚠️ `WorkflowStepRun` + `audit_events`, not modelled as graph nodes |
| CRM Record / ERP Record | ⚠️ present as raw snapshots, not as graph entities |

**8 of 25 present, 3 partial, 14 absent.**

---

## The real constraint

Adding entity types is not blocked by the schema — `CanonicalEntity` accepts any type string.
It is blocked upstream, by two things:

1. **`data_source_sync` ignores `connector_id` and always syncs the demo company**
   (`persistent_runtime.py:272-278`). No matter what a customer connects, the graph is
   populated from `mock_data`. This is roadmap SB-2 and is the actual blocker.
2. **The opportunity taxonomy is compiled in.** `SignalId` is a five-value `Literal`
   (`agents/contracts.py:7-13`) and metric derivation matches Turkish product names as
   strings (`metrics.py:191-210`). Even with richer entities, the diagnostic can only express
   five predetermined opportunities. This is SB-1 and decision D8.

Building out entity types before those two are fixed would add unreachable structure.

---

## Open decisions

1. **Entity type vocabulary — closed or open?** A closed enum is validatable and lets the
   diagnostic reason about types; an open string set lets a connector introduce a type without
   a code change. The capability registry precedent (code-defined, validated) argues for
   closed.

2. **Which entities does the *diagnostic* need?** Not all 25 serve the current product. The
   diagnostic consumes accounts, opportunities, products, invoices and contacts. Competitor
   and Campaign are needed by PRD modules (§7.11, §7.13) that do not exist. Sequence entity
   work behind the module that consumes it rather than building the full graph speculatively.

3. **Are Recommendation and Agent Action graph entities or run artefacts?** They are currently
   run artefacts. Promoting them into the graph would let later runs reason over earlier
   recommendations — which is what "context first" (PRD §4.1) implies — but it makes run
   output and canonical state overlap, and the ownership boundary in ADR-0001 would need
   revisiting.

4. **Identity resolution.** With one synthetic connector there are no duplicates. With two
   real sources there will be: the same account from CRM and ERP. Entity matching, merge
   rules and merge provenance are unsolved and are a prerequisite for any second connector.
   PRD §14 already lists `Canonical entity match accuracy` as a success metric.

5. **Where does Company live?** Currently installation configuration, not a graph node. Under
   ADR-0032's deployment-level tenancy that is coherent — one installation, one company — but
   it means the graph has no root node for the customer itself.

---

## Suggested order

```
SB-2 (real connector data reaches the graph)
  └── identity resolution rules (decision 4)
        └── entity types required by the next module (decision 2)
              └── D8 / SB-1 (signal taxonomy stops being a Literal)
```

---

## Related

- ADR-0001 — OKF / PostgreSQL ownership boundary
- ADR-0032 — tenancy, which determines whether Company is a graph node
- `docs/REMEDIATION_ROADMAP.md` — SB-1, SB-2, D8
