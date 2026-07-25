# ADR-0022: Audit Report Runde 4 Low Priority Cleanup

## Status
Accepted

## Context
During the technical audit documented in `docs/AUDIT_RAPORT.md`, 6 low-priority maintenance tasks were identified:
1. **Bulgu 1.1**: Re-verified that README architecture links cleanly resolve to `docs/SYSTEM_ARCHITECTURE.md`.
2. **Bulgu 1.3**: Simplified observability docker compose instruction in `docs/OPERATIONS_RUNBOOK.md` to `docker compose --profile observability up -d`.
3. **Bulgu 6.3**: Deleted unreferenced legacy DBOS helper scripts (`scripts/cleanup_dbos.py`, `scripts/watch-workflow-restarts.sh`).
4. **Bulgu 7.4**: Moved orphan `docs/NEW_ARCHITECTURE.yaml` specification to `docs/archive/NEW_ARCHITECTURE.yaml`.
5. **Bulgu 7.5 & Bulgu 7.6**: Linked authoritative `docs/DOMAIN_CONTRACTS.md` and `docs/PRODUCT_ROADMAP_TO_GOAL.md` documents in `README.md`.

## Decision
1. Simplify observability startup instructions in `docs/OPERATIONS_RUNBOOK.md`.
2. Remove deprecated DBOS helper scripts from `scripts/`.
3. Move `NEW_ARCHITECTURE.yaml` into `docs/archive/`.
4. Include `DOMAIN_CONTRACTS.md` and `PRODUCT_ROADMAP_TO_GOAL.md` in root `README.md`.

## Consequences
- Operational runbook contains clear, single-command observability startup instructions.
- Repository is free of orphan YAML files and deprecated DBOS scripts.
- Navigation through root `README.md` provides complete links to domain contracts and product roadmaps.
- All 32 findings across Rounds 1-4 of the technical audit report are 100% resolved.
