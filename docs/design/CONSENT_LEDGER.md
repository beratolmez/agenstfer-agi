# Consent Ledger — Design Skeleton

**Status:** Not implemented. This is a scoping document, not a specification.
**Source requirement:** PRD §6.4, §10; cited in PRD §15.6 as a differentiator against n8n.

Written because the Consent Ledger had no design record — no code, no schema, no ADR.
`rg -i "consent"` across `apps/api/agi_server` returns nothing.

---

## Why it does not exist yet, and why that is currently fine

The MVP is read-only toward external systems (ADR-0004): no email, no SMS, no calls, no
messaging. A consent ledger governs outbound contact, and there is no outbound contact.

That makes this a **sequencing** question, not an oversight — but it is a hard prerequisite.
The moment any outbound capability is added, consent must already be in place, because a
system that can contact people before it can record permission to contact them is precisely
the "uncontrolled outbound automation tool" PRD §17 says the product must not be.

---

## What the PRD requires

PRD §6.4 lists thirteen fields per contact:

email permission · phone permission · SMS permission · WhatsApp permission · social media
contact state · opt-in source · opt-in time · opt-out time · do-not-call state · consent
evidence · consent expiry · legal basis · available channels

PRD §10 adds the operational surface: opt-out management, do-not-call list checking, consent
evidence retention, data-source tracking, purpose-of-use, erasure requests, access requests,
and auditable action history.

---

## What the codebase already gives it

The evidence layer is a good fit for `consent evidence`, and reusing it is the main design
opportunity here rather than inventing a parallel mechanism:

| Requirement | Existing mechanism |
|---|---|
| Consent evidence | `EvidenceItem` + content-addressed raw vault — an opt-in record is exactly the kind of immutable, locator-addressed artefact this layer already handles |
| Data source tracking | `DataSource`, `RawSnapshot`, `SourceMapping` |
| Auditable history | `audit_events` |
| Approval for risky actions | Approval Center |
| Contact entity | `CanonicalEntity` of type `contacts` (`connectors/demo.py`) — currently carries only `role` and `email` (`domain/demo.py:48-55`) |

---

## Open decisions

1. **Where does consent live?** A dedicated `consent_records` table keyed by contact, or
   `CanonicalFact` rows against the contact entity? The latter reuses evidence binding and
   validity-time handling that already exist; the former is easier to query and to enforce a
   uniqueness constraint per (contact, channel).

2. **Which channels are in scope for v1?** The PRD lists five. Implementing all five before
   any of them can be used is speculative. A defensible v1 is *record and expose* consent for
   whichever channel the first outbound capability targets, with the schema shaped to admit
   the rest.

3. **How does consent enter the system?** The MVP is read-only, so consent must be ingested
   from a customer's CRM rather than captured by this product. That makes it a connector
   mapping problem: which CRM fields map to which consent field, and what happens when a
   source has no consent data at all. **Absence must mean "no permission", never "unknown, so
   proceed".**

4. **Expiry semantics.** Does an expired consent block, or downgrade to requiring approval?
   Regional rules differ, and PRD §10 asks for region-aware behaviour.

5. **Legal basis vocabulary.** Fixed enum (consent / legitimate interest / contract) or free
   text? An enum is enforceable in policy; free text is not.

6. **Erasure.** PRD §10 requires personal-data erasure on request. This conflicts with the
   immutable raw vault: snapshots are content-addressed and never mutated. Deciding how
   erasure interacts with immutable evidence is the hardest question on this list and should
   be settled before any personal data beyond the demo set is ingested.

---

## Dependency order

```
ADR-0004 relaxed (an outbound capability is approved)
  └── Consent Ledger schema + CRM ingestion mapping
        └── Policy Engine consent dimension (docs/design/POLICY_ENGINE.md)
              └── Outbound draft / sequence module (PRD §7.7)
```

Nothing below the first line should start before the line above it is settled.

---

## Related

- ADR-0004 — no external write in MVP
- `docs/design/POLICY_ENGINE.md` — consumer of consent state
- `docs/THREAT_MODEL.md` — personal-data handling and retention
