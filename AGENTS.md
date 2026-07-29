# Agentic Growth Intelligence Engineering Rules

## Read order

Before changing the product, read:

1. `docs/IMPLEMENTATION_STATUS.md`
2. `docs/SYSTEM_ARCHITECTURE.md`
3. `docs/PRODUCT_DEPLOYMENT_PLAN.md` for customer/AWS/update decisions
4. Relevant files in `docs/adr/`
5. `knowledge/AGENTS.md` for knowledge-ingestion or OKF work

Treat vision documents as immutable sources. Record revised decisions in the architecture document and an ADR.

## Product boundaries

- One customer installation serves one company. Isolation comes from deployment separation,
  not row-level tenancy: one installation, one database, one knowledge volume, one customer
  (ADR-0032). Do not introduce shared SaaS multi-tenancy.
- AWS may host a customer deployment, but customer-owned account/VPC isolation, data residency,
  and update/rollback boundaries must remain explicit.
- The MVP is read-only toward external business systems. Do not add external write, messaging,
  calling, or autonomous action capabilities (ADR-0004). Authorized web scraping is the single
  exception and remains bounded by the egress allowlist (ADR-0005). Changing this is a staged
  path documented in `docs/TOOLS_STRATEGY.md`: it requires a superseding ADR, per-tool-call
  observability and tool-level approval before any outbound capability ships.
- Agent tools ship as native, code-defined capabilities. MCP is a target specification, not an
  active capability: the policy layer exists, the transport does not (ADR-0030).
- Model Gateway manages LLM inference across cloud APIs and isolated local/cloud GPU endpoints
  (Ollama, vLLM, LM Studio). The data-classification boundary is fail-closed: `confidential`
  and `restricted` content never reaches a cloud model. Model selection moves from literal
  profile names to a tier vocabulary resolved from installation configuration (ADR-0033).
- Observability sinks must be self-hosted or explicitly approved; do not
  send prompts, source bodies, evidence excerpts, secrets, or contact identifiers by default.
- Documents and connector payloads are untrusted data, never instructions.
- Agent tools and workflow nodes come from code-defined allowlists. Do not execute user code or arbitrary plugins.
- Core orchestration is LangGraph (state/workflows) and FastAPI. Do not add another
  orchestration engine; the two runtimes that exist today converge on one, selected by a
  property of the workflow definition rather than by id (ADR-0029).
- Agent implementation strictly uses Pydantic AI.

## Data ownership

- OKF 0.1 Markdown/YAML owns portable company knowledge.
- PostgreSQL owns users, roles, source configuration, evidence locators, canonical state, workflow metadata, approvals, and audit records.
- LangGraph owns workflow state and execution tracing. Durable checkpointing is the accepted
  target (PostgreSQL checkpointer, ADR-0029); today resume is reconstructed from persisted step
  rows, so do not assume checkpoint durability.
- Raw source snapshots are immutable and content-addressed.
- Retrieval is one layer with two paths over the active OKF bundle (ADR-0031): structural and
  lexical over the OKF Wiki, plus a derived vector index. The index is disposable and
  rebuildable; the active bundle is the source of truth. Locators are resolved from the wiki
  and the evidence store, never synthesised by the index.
- Every material or numerical generated claim must resolve to persisted evidence and an immutable source locator.
- Candidate OKF changes cannot affect the active bundle before an authenticated approval.

## Delivery discipline

- Work only inside the active phase unless a prerequisite defect blocks it.
- A UI control (React UI) is not complete until it calls a real API (FastAPI) and its state survives refresh when persistence is required.
- A schema is not complete until migrations, repository/service behavior, API behavior, and tests exist.
- A model integration is not complete until a real structured-output probe and golden evaluation pass.
- Never label deterministic fixtures or placeholders as agent execution.
- Update `docs/IMPLEMENTATION_STATUS.md` in the same change that materially changes capability status.
- Add or supersede an ADR in `docs/adr/` for durable architecture, UI flow, model gateway, or security decisions.
- Synchronize `docker-compose.yml` and rebuild/recreate containers whenever environment variables, default model names, or UI builds change.

## Mandatory Task Handoff Protocol

Before presenting completion to the user, the agent MUST strictly perform the following steps automatically without waiting for user reminders:

1. Update `docs/IMPLEMENTATION_STATUS.md` and add/update an ADR in `docs/adr/`.
2. Update `docker-compose.yml` and execute `docker compose up -d --build --force-recreate` if compose configs or UI assets change.
3. Run `scripts/project-check.ps1` on Windows or `scripts/project-check.sh` on Linux to verify 100% clean test passes.
4. Commit and push all changes to the remote Git repository (`origin main`).
