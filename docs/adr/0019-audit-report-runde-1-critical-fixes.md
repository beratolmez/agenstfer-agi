# ADR-0019: Audit Report Runde 1 Critical Fixes

## Status
Accepted

## Context
During the technical audit documented in `docs/AUDIT_RAPORT.md`, four critical functional and security issues were identified:
1. **Bulgu 3.1**: `App.tsx` possessed a race condition in `SetupWizard.onComplete` where `navigate("dashboard")` executed before `api.setupStatus()` resolved, causing state re-evaluations to loop back into `SetupWizard`.
2. **Bulgu 3.7**: `SetupWizard.tsx` and backend `main.py` setup progress endpoints submitted and set 10 dummy steps even though the onboarding UI is structured into 5 concrete steps.
3. **Bulgu 4.1 & Bulgu 2.4**: `docker-compose.yml` assigned the `app` container to the external `egress` network (`networks: [core, egress]`), creating a potential security bypass around the mandatory `egress-gateway` (Squid proxy) required by ADR-0005.
4. **Bulgu 2.2**: `docs/SYSTEM_ARCHITECTURE.md` diagram and feature comparison table listed LangGraph, ChromaDB RAG, and MCP Gateway as unmigrated "Target" items, creating a discrepancy with `docs/IMPLEMENTATION_STATUS.md` where Phases 1-16 were verified completed.

## Decision
1. **App.tsx Race Condition Fix**: Await `api.setupStatus()` inside `SetupWizard.onComplete` before executing `navigate("dashboard")`.
2. **Setup Step Alignment**: Align `/api/setup/status` and `/api/setup/progress` step names and bounds with the 5 actual setup wizard steps (`completed_steps: [1, 2, 3, 4, 5]`).
3. **Egress Proxy Network Isolation**: Remove `egress` network from `app` service in `docker-compose.yml`, leaving `app` strictly on `networks: [core]`. `app` now routes all internet traffic through `http://egress-gateway:3128`.
4. **Architecture Documentation Alignment**: Update `docs/SYSTEM_ARCHITECTURE.md` to reflect LangGraph StateGraph engine, ChromaDB with lexical fallback, approved MCP client gateway, and Vanilla CSS as active baseline components.

## Consequences
- Onboarding completion cleanly navigates to Dashboard without re-triggering setup wizard renders.
- Installation state in database truthfully records completed steps 1 through 5.
- Container network topology strictly enforces egress proxy boundaries.
- Architecture documentation matches actual code baseline.
