# ADR-0021: Audit Report Runde 3 Medium Priority Cleanup

## Status
Accepted

## Context
During the technical audit documented in `docs/AUDIT_RAPORT.md`, 9 medium-priority issues were identified regarding missing endpoint implementations, incomplete TypeScript type contracts, proxy server performance/websocket headers, docker build context optimization, and architecture terminology:
1. **Bulgu 3.3**: `api.ts` defined `filePreview: (sourceId) => GET /api/sources/${sourceId}/preview`, but the backend lacked a matching GET endpoint.
2. **Bulgu 3.4**: `WorkflowRunDetail` TypeScript interface lacked extended fields (`idempotency_key`, `evidence_ids`, `agent_versions`, `token_usage`, `artifacts`, `steps`) returned by backend `workflow_run_detail`.
3. **Bulgu 4.2**: Nginx configuration lacked WebSocket upgrade headers, gzip compression, and static asset caching policies.
4. **Bulgu 6.1 & Bulgu 6.2**: `apps/frontend` legacy mock UI directory was included in build tracking without `.dockerignore` filtering.
5. **Bulgu 7.1 & Bulgu 7.2**: Stub test mock classes lacked explicit docstrings explaining intent for vector search test monkeypatches.
6. **Bulgu 7.3**: `PROJECT_ARCHITECTURE.md` referenced outdated Kubernetes/ECS multi-cluster concepts instead of the active Docker Compose customer-isolated single-host architecture.

## Decision
1. Implement `GET /api/sources/{source_id}/preview` in `apps/api/agi_server/main.py`.
2. Expand `WorkflowRunDetail` in `apps/web/src/types.ts` with `WorkflowRunStepDetail` and `WorkflowRunArtifactDetail` interfaces.
3. Harden `infra/proxy/nginx.conf` with `Upgrade`/`Connection` headers, `gzip` compression, and `/assets/` caching.
4. Exclude `apps/frontend/` in `.dockerignore`.
5. Add explicit intent comments to test mock fixtures and fallback exception blocks.
6. Update `docs/PROJECT_ARCHITECTURE.md` mapping table to Docker Compose single-host reference deployment.

## Consequences
- Existing sources can be previewed by ID via `GET /api/sources/{source_id}/preview`.
- Frontend TypeScript types reflect full execution step and artifact payloads.
- Reverse proxy supports WebSocket connections, gzip compression, and asset caching.
- Build context and architecture documentation cleanly align with production baseline.
