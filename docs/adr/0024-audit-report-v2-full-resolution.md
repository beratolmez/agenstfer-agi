# ADR-0024: Audit Report Round 2 Full Resolution & Workflow/Docker Alignment

- **Status**: Accepted
- **Date**: 27 July 2026

## Context

During a secondary comprehensive technical audit of the codebase, 11 technical debt items and architectural discrepancies were identified across workflow runtime selection, API error handling, Docker Compose definitions, and legacy service bundling.

## Decisions

1. **Diagnostic LangGraph Runtime Alignment**: Updated `apps/api/agi_server/workflow/persistent_runtime.py` to include `"growth-diagnostic"` in the `LangGraphWorkflowEngine` selection filter so cloned user diagnostic runs execute strictly under LangGraph.
2. **Deprecated DBOS Error Cleaning**: Removed the remaining `settings.enable_dbos` check from `main.py` `approval_decision` endpoint and `test_workflow_platform.py`.
3. **Model Download Compose Fix**: Updated `docker-compose.model-download.yml` with standalone ports (`11434`), volume mounts (`ollama_data`), and network specifications.
4. **AWS Production Compose Alignment**: Updated `infra/aws/docker-compose.prod.yml` to use `AGI_CLOUD_*` environment variables and correct Nginx volume path.
5. **Proxy Egress Allowlist Alignment**: Updated `NO_PROXY` in `docker-compose.cloud.yml` to include `web-proxy`.
6. **Workspace & Dockerfile Cleanup**: Removed legacy `apps/services/*` workspace member definitions from `pyproject.toml` and removed `COPY apps/services/` from `Dockerfile`.
7. **Durable Seam Documentation**: Updated `_ensure_durable_workflow` stub in `persistent_runtime.py` with explanatory docstring.

## Consequences

- All growth diagnostic runs (including custom model profile clones) execute through LangGraph StateGraph engine.
- Approval Center decision endpoints operate cleanly without AttributeError risks.
- Docker compose overlays and production deployment manifests match the current single-host reference deployment architecture.
- Docker build context and uv workspace configurations are clean of unintegrated legacy microservice stubs.
