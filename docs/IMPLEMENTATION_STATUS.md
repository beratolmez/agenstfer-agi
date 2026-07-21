# Implementation Status

Last verified: 21 July 2026

This document is the authoritative statement of what the repository actually does. 

## Implemented and verified

### Platform and trust boundary

- [x] FastAPI exposes the backend logic.
- [x] React UI exposes the frontend dashboard and chat at `http://localhost:5173` (Vite) / production port.
- [x] Database uses PostgreSQL for app state and LangGraph checkpointing.

### Ingestion, evidence, and knowledge

- [x] Mock data ingestion via `/api/setup` endpoint implemented.
- [x] RAG Service uses ChromaDB for generating and querying markdown embeddings.
- [x] Old `qmd` and durable storage lifecycles completely replaced.

### Agents, diagnostic, and workflows

- [x] LangGraph manages the orchestrator state machine.
- [x] Pydantic AI is used for structured output parsing.
- [x] Nodes include Researcher, Analyst, Reviewer, and KDS AI ABS specialized growth nodes.
- [x] Model Gateway manages LLM inference flexibly across Gemini API and Local/Cloud GPU model servers (Ollama, vLLM, LM Studio).
- [x] Chat loop exposes streamable or stateful returns via `/api/chat`.
- [x] Human-in-the-loop workflow approval is integrated using LangGraph `interrupt_before`/`interrupt_after`.
- [x] Golden evaluation tests implemented and verifying agent claims against ChromaDB mock data.

### Product journey

- [x] Setup progress `/api/setup` successfully sets up ChromaDB.
- [x] Chat interface `/api/chat` successfully orchestrates the Analyst and Reviewer agents.
- [x] Dashboard UI accurately displays agent states and reports.
- [x] Single authoritative architecture documentation (`docs/SYSTEM_ARCHITECTURE.md`) unified across all 3 visual diagrams and system rules.

### Security and operations

- [x] No external write operations permitted in MVP.
- [x] Data privacy boundaries strictly enforced on Model Gateway cloud calls.
- [x] Replaced complex legacy retry/durable mechanisms with LangGraph state checkpointing in PostgreSQL.
- [x] Telemetry and observability integrated with self-hosted Langfuse sink.

## Release blockers and deliberately incomplete acceptance

- [ ] Provide more robust tests for the LangGraph StateGraph edges and branches.
- [ ] Connect real external CRM/ERP for live sync rather than just mock markdown data.

## Commercial product architecture alignment

The migration to LangGraph/Pydantic AI and the unification of AWS Control Plane, Container Cluster, Model Gateway, and KDS AI ABS Agent Nodes marks the finalized architecture alignment for the MVP.

