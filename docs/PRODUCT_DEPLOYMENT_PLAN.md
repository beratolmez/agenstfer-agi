# Product Deployment and Commercialization Plan

Status: Active target architecture
Last updated: 17 July 2026

This document turns the manager's original architecture plan (archived at `docs/archive/NEW_ARCHITECTURE_PLAN.md`) into an executable product direction.
The product is sold and updated by the vendor, but each customer receives an isolated installation
serving one company. Shared SaaS tenancy is not part of the current product boundary.

## 1. Product model

- The vendor owns the product code, agent/capability catalog, workflow templates, release process,
  and support lifecycle.
- A customer installation owns its company data, OKF Git history, PostgreSQL state, model secrets,
  and operational traces. The system relies on the Gemini API for generative operations.
- Customer environments do not share databases, knowledge bundles, model prompts, or Langfuse data.
- Updates are pull-based, versioned, signed, backed up, and reversible. A customer administrator or
  an approved operator chooses when an update is applied.
- Customer-specific connector and workflow requests are implemented as reviewed product extensions;
  customers do not upload arbitrary code or plugins.

## 2. Deployment editions

The implementation must keep the application contract independent of the deployment edition.

| Edition | Control plane | LLM Integration | Operator | Initial status |
|---|---|---|---|---|
| Local private | Customer Docker host | Gemini API | Customer or vendor | Current MVP reference |
| Managed AWS private | Dedicated AWS account/VPC | Gemini API | Vendor | First production candidate |
| Customer AWS private | Customer AWS account/VPC | Gemini API via outbound gateway | Customer with vendor support | Target |
| Split private | AWS control plane | Gemini API over private service link | Vendor | Target |

AWS is therefore a deployment option that may become the first production profile; it is not a
semantic change to the OKF/PostgreSQL ownership boundary.

## 3. Control plane and data plane

The control plane contains the React web console, FastAPI backend, authentication, PostgreSQL operational state,
LangGraph workflow runtime, approval center, release metadata, and model policy. The data/model plane
contains raw snapshots, the OKF bundle, canonical evidence, ChromaDB indexes, and API proxies.

Agents never connect to PostgreSQL or an ERP/CRM directly. They receive capability-scoped, bounded
results from the control plane. The FastAPI backend is the only component that resolves provider,
network, classification, redaction, and structured-output policy before hitting the Gemini API.

## 4. AWS target topology

The first AWS design should use one customer-isolated VPC:

- Public subnet: customer-approved ingress/load balancer for React UI.
- Private application subnet: FastAPI backend and LangGraph state workers.
- Private data subnet: RDS PostgreSQL and encrypted object storage for raw/artifact backups.
- Private inference subnet: Outbound proxy or NAT gateway for Gemini API requests.
- Optional egress subnet: allowlisted provider access only; disabled by default.
- Observability subnet or internal service: self-hosted Langfuse and/or Jaeger.

The repository's Compose topology remains the local reference implementation. AWS IaC, image
promotion, TLS termination, backup policy, and customer account ownership are release engineering
work and must not be implied by the Python application alone.

## 5. Gemini API Integration

The default commercial assumption is that the product relies on the Gemini API. The application must never expose model interactions
on a public API port; it connects through the FastAPI backend serving as an internal Model Gateway.

For the first product release, prefer this isolation mode:

1. **Dedicated Gemini API key and quota per customer:** simplest data and performance boundary for a small-company
   product, ensuring cost and rate limit isolation.

Shared API credentials across customers is not an MVP assumption. If it is later introduced, the
vendor must add tenant-aware scheduling, encrypted request/result handling, rate limits, model cache
isolation, noisy-neighbor protection, and a new threat model. Access to Gemini API
is routed through an outbound inference gateway.

A failed model request must not silently fall back to an unapproved cloud provider. The backend records
the selected model profile, network path, classification, redaction, and policy
outcome for every call.

## 6. Observability

OpenTelemetry remains the instrumentation boundary. Jaeger is the minimal local diagnostic sink;
Langfuse is the product-oriented trace/evaluation sink. Langfuse must run per customer or in an
explicitly approved isolated environment.

Allowed telemetry includes provider/model, agent/workflow versions, duration, token totals, retry
counts, validation results, evidence counts, classifications, and safe hashes. Prompt bodies,
source bodies, evidence excerpts, secrets, and contact identifiers are excluded by default.

Before shipping a Langfuse profile, verify self-hosted telemetry settings, retention, access control,
backup, and licensing for any non-OSS features. The integration must not weaken the no-egress policy.

## 7. Customer workflow model

The vendor supplies immutable, tested templates such as Growth Diagnostic. A customer Admin may
clone a template, edit a draft, configure safe conditions/schedules, dry-run it, and publish an
immutable version. Analysts run published workflows; Approvers decide candidate knowledge changes.

Customer authoring is limited to the code-defined node and capability catalog via React UI. Arbitrary code,
unrestricted network tools, arbitrary MCP servers, direct SQL, and external write nodes are not
available in the product.

New connector/capability types are vendor-delivered product releases. A known ERP/CRM first-party
connector is preferred over a generic MCP bridge. MCP may be added later behind the same allowlist,
classification, approval, idempotency, audit, and rollback controls.

## 8. Bounded task orchestration

The current Growth Diagnostic remains a deterministic four-agent workflow in LangGraph. A later
`BoundedTaskOrchestrator` may support dynamic worker planning for knowledge-gap resolution,
segmented analysis, or report completeness checks via Pydantic AI.

The orchestrator may propose a typed task plan, but runtime policy enforces:

- maximum workers per round,
- maximum rounds,
- timeout and token/cost budgets,
- code-defined worker profiles,
- capability and data-classification scope,
- typed completion criteria,
- durable LangGraph task/round state,
- final evidence review and human approval where required.

Workers may not create arbitrary workers, expand tools, execute code, or perform external writes.
The first implementation should be post-MVP and should not replace the deterministic diagnostic
until it passes a separate evaluation and recovery gate.

## 9. Release and update lifecycle

1. Build and test a versioned product image set.
2. Generate SBOM, vulnerability report, migration plan, and release notes.
3. Sign and publish the approved image/package bundle.
4. Customer backup and preflight checks run before update.
5. Migration and health checks run in the customer environment.
6. Smoke tests verify authentication, model readiness, evidence resolution, workflow start, and
   observability.
7. Rollback restores the previous image and compatible database/knowledge backup when required.

Vendor support should receive content-safe diagnostics by default. Any remote support session or
central telemetry must be an explicit customer-controlled opt-in.

## 10. Product sequencing

### Release MVP

- Single-company isolated installation.
- Docker Compose reference deployment.
- AWS deployment decision and reference topology documented, not yet assumed complete.
- Read-only CRM/ERP/file connectors.
- OKF/evidence/ChromaDB RAG, deterministic Growth Diagnostic in LangGraph, approval, export, backup/restore.
- Self-hosted OpenTelemetry/Jaeger; Langfuse integration behind an opt-in observability profile.

### First product release after MVP

- One selected AWS runtime and IaC package.
- Customer installation/update/rollback automation.
- Self-hosted Langfuse operational package.
- First real read-only CRM/ERP connector.
- Capacity profile and safe diagnostic concurrency policy.

### Later platform waves

- Bounded task orchestration and controlled fan-out workers.
- MCP adapters for reviewed partner systems.
- Controlled write actions only after separate security, consent, rollback, and legal decisions.
- ERP/CRM, reporting, social, website, and other business modules.

## 11. Open decisions for product and DevOps

- Is the first AWS edition vendor-managed or customer-owned?
- Which AWS runtime is first: ECS, EKS, or a simpler EC2/Compose profile?
- Are we dedicating Gemini API quotas per customer?
- Which region and data-residency boundary applies for Gemini API processing?
- Does AWS reach the Gemini API through a private service link, VPN, or an outbound gateway?
- Who owns incident response for API quotas and capacity planning?
- What customer support telemetry and Langfuse retention are acceptable?
- What starter capacity profile is promised for small companies?
- Which first CRM/ERP is selected by the design partner?
