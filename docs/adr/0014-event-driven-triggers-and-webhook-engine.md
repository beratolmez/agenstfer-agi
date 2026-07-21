# ADR-0014: Event-Driven Triggers & Webhook Ingestion Engine

* Status: Accepted
* Date: 2026-07-21
* Deciders: Antigravity AI Team & Product Management

## Context and Problem Statement

B2B companies require automated growth intelligence workflows to run instantly when business events occur (e.g. CRM account updates, inbound lead form submissions, competitor news signals) rather than relying exclusively on manual button clicks or static periodic schedules.

## Decision Drivers

- **Automation & Responsiveness**: Minimize time-to-insight when new lead or competitor signals arrive.
- **Auditability & Traceability**: Record every incoming webhook payload, matched trigger rule, and initiated workflow run.
- **Read-Only & Safety Boundary**: Webhook handlers process incoming event data without granting external write access to business systems.

## Considered Options

1. **Option 1**: Event-Driven Trigger Engine with REST Webhook Ingestion (`POST /api/webhooks/{source_id}`) and Trigger Rule Registry.
2. **Option 2**: Manual execution only via React UI.
3. **Option 3**: Poll business systems on fixed cron intervals only.

## Decision Outcome

Chosen Option: **Option 1**.

### Consequences

- **Positive**:
  - Growth workflows run automatically upon event arrival (`crm.account_updated`, `inbound.form_submitted`, `competitor.signal_detected`, `lead.opportunity_detected`).
  - React UI **EventPanel** provides live payload inspection, trigger rule management, and event audit streams.
  - Audit log tracks all webhook receipts and triggered workflow executions.
- **Negative / Risks**:
  - High webhook volume requires rate-limiting and payload validation.
