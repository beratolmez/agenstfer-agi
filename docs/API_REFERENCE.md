# API Reference

**Generated from the live FastAPI route table on 28 July 2026** (74 endpoints).
Regenerate after changing routes — see [Regenerating](#regenerating).

All paths are served under the `web-proxy` on port 8080. Every `/api/*` request except the
bootstrap and login endpoints requires an authenticated session cookie plus an
`X-CSRF-Token` header on state-changing methods (`http_security.py`).

## Roles

`bootstrap_admin` grants all three roles at once (`security.py:98`). There is no role
hierarchy: `require_role("admin")` matches the literal role only (`security.py:176`).

| Role | Intent |
|---|---|
| `admin` | Model gateway, users, agent and workflow publication, connector tests |
| `analyst` | Start diagnostics and workflow runs, edit drafts |
| `approver` | Decide approvals and OKF candidates |
| `session` | Any authenticated user |
| — | No explicit role dependency; still behind the session middleware unless `AGI_DEMO_NO_AUTH` is set |

> `AGI_DEMO_NO_AUTH=true` (the `dev` and `e2e` compose overlays) disables the session gate
> entirely. It is rejected in production by a settings validator (`config.py:73-74`).

## Conventions

- **Idempotency:** run-starting endpoints take an `Idempotency-Key` header; replaying a key
  returns the existing run rather than starting a second one.
- **Errors:** a uniform envelope — `{"error": {"code", "message", "details", "request_id"}}`.
  Workflow failures additionally carry content-safe `provider`, `model`, `profile`,
  `http_status` and `node_id` in `error_json` (`logging_utils.py:27-100`).
- **Untrusted input:** connector payloads, uploaded documents and webhook bodies are data,
  never instructions. Webhook bodies are persisted to `EventInbox` before any matching.

## Endpoints

### `/agents`

| Path | Method | Role | Notes |
|---|---|---|---|
| `/api/agents` | GET | — |  |
| `/api/agents/{agent_id}/draft` | PUT | admin |  |
| `/api/agents/{agent_id}/versions` | GET | — |  |
| `/api/agents/{agent_id}/versions/{version}` | GET | admin | Return the editable prompt only to an authenticated administrator. |
| `/api/agents/{agent_id}/versions/{version}/clone` | POST | admin |  |
| `/api/agents/{agent_id}/versions/{version}/publish` | POST | admin |  |

### `/approvals`

| Path | Method | Role | Notes |
|---|---|---|---|
| `/api/approvals` | GET | — |  |
| `/api/approvals/{approval_id}/decision` | POST | approver |  |

### `/auth`

| Path | Method | Role | Notes |
|---|---|---|---|
| `/api/auth/bootstrap` | POST | — |  |
| `/api/auth/login` | POST | — |  |
| `/api/auth/logout` | POST | session |  |
| `/api/auth/me` | GET | session |  |

### `/capabilities`

| Path | Method | Role | Notes |
|---|---|---|---|
| `/api/capabilities` | GET | — |  |

### `/dashboard`

| Path | Method | Role | Notes |
|---|---|---|---|
| `/api/dashboard` | GET | — |  |

### `/diagnostics`

| Path | Method | Role | Notes |
|---|---|---|---|
| `/api/diagnostics/run` | POST | analyst | Compatibility start view; production execution always uses a published workflow. |

### `/docs`

| Path | Method | Role | Notes |
|---|---|---|---|
| `/api/docs` | GET | — |  |

### `/evidence`

| Path | Method | Role | Notes |
|---|---|---|---|
| `/api/evidence/{evidence_id}` | GET | — |  |

### `/health`

| Path | Method | Role | Notes |
|---|---|---|---|
| `/api/health` | GET | — |  |

### `/knowledge`

| Path | Method | Role | Notes |
|---|---|---|---|
| `/api/knowledge` | GET | — |  |
| `/api/knowledge/{concept_path:path}` | GET | — |  |

### `/model`

| Path | Method | Role | Notes |
|---|---|---|---|
| `/api/model/status` | GET | — | Expose configuration state without ever returning the provider secret. |

### `/models`

| Path | Method | Role | Notes |
|---|---|---|---|
| `/api/models/configure` | POST | admin |  |
| `/api/models/discover` | POST | admin |  |
| `/api/models/probe` | POST | admin |  |
| `/api/models/profiles` | GET | — | List code-defined profiles and configuration state without returning secrets. |

### `/okf`

| Path | Method | Role | Notes |
|---|---|---|---|
| `/api/okf/approve` | POST | approver |  |
| `/api/okf/candidates` | GET | — |  |
| `/api/okf/candidates/{candidate_id}/decision` | POST | approver |  |
| `/api/okf/candidates/{candidate_id}/diff` | GET | — |  |
| `/api/okf/diff` | GET | — |  |
| `/api/okf/export` | GET | analyst |  |
| `/api/okf/import` | POST | admin |  |
| `/api/okf/validate` | GET | — |  |

### `/openapi.json`

| Path | Method | Role | Notes |
|---|---|---|---|
| `/api/openapi.json` | GET | — |  |

### `/runs`

| Path | Method | Role | Notes |
|---|---|---|---|
| `/api/runs` | GET | — |  |
| `/api/runs/{run_id}` | GET | — |  |
| `/api/runs/{run_id}/artifacts/{artifact_id}` | GET | — |  |
| `/api/runs/{run_id}/cancel` | POST | analyst |  |
| `/api/runs/{run_id}/retry` | POST | analyst |  |

### `/setup`

| Path | Method | Role | Notes |
|---|---|---|---|
| `/api/setup/demo` | POST | admin |  |
| `/api/setup/progress` | GET | — |  |
| `/api/setup/progress` | PUT | admin |  |
| `/api/setup/status` | GET | — |  |

### `/sources`

| Path | Method | Role | Notes |
|---|---|---|---|
| `/api/sources` | GET | — |  |
| `/api/sources/demo/sync` | POST | admin |  |
| `/api/sources/files/preview` | POST | admin |  |
| `/api/sources/sync-runs` | GET | — |  |
| `/api/sources/test-db` | POST | admin |  |
| `/api/sources/test-mcp` | POST | admin |  |
| `/api/sources/{source_id}/mapping` | POST | admin |  |
| `/api/sources/{source_id}/preview` | GET | — |  |
| `/api/sources/{source_id}/sync` | POST | admin |  |

### `/triggers`

| Path | Method | Role | Notes |
|---|---|---|---|
| `/api/triggers/events` | GET | — |  |
| `/api/triggers/rules` | GET | — |  |

### `/users`

| Path | Method | Role | Notes |
|---|---|---|---|
| `/api/users` | GET | admin |  |
| `/api/users` | POST | admin |  |
| `/api/users/{user_id}/roles` | PUT | admin |  |

### `/webhooks`

| Path | Method | Role | Notes |
|---|---|---|---|
| `/api/webhooks/{source_id}` | POST | session |  |

### `/workflow-schedules`

| Path | Method | Role | Notes |
|---|---|---|---|
| `/api/workflow-schedules` | GET | — |  |
| `/api/workflow-schedules/{schedule_id}` | PUT | admin |  |

### `/workflows`

| Path | Method | Role | Notes |
|---|---|---|---|
| `/api/workflows` | GET | — |  |
| `/api/workflows` | POST | analyst |  |
| `/api/workflows/default` | GET | — |  |
| `/api/workflows/dry-run` | POST | analyst |  |
| `/api/workflows/templates` | GET | — |  |
| `/api/workflows/validate` | POST | — |  |
| `/api/workflows/{workflow_id}/draft` | PUT | analyst |  |
| `/api/workflows/{workflow_id}/versions` | GET | — |  |
| `/api/workflows/{workflow_id}/versions/{version}` | GET | — |  |
| `/api/workflows/{workflow_id}/versions/{version}/clone` | POST | analyst |  |
| `/api/workflows/{workflow_id}/versions/{version}/dry-run` | POST | analyst |  |
| `/api/workflows/{workflow_id}/versions/{version}/publish` | POST | admin |  |
| `/api/workflows/{workflow_id}/versions/{version}/run` | POST | analyst |  |
| `/api/workflows/{workflow_id}/versions/{version}/schedules` | POST | admin |  |

## Regenerating

This file is generated from the running application, so it cannot drift from the routes:

```bash
uv run python - <<'PY'
import sys; sys.path.insert(0, "apps/api")
from agi_server.main import app
for r in app.routes:
    methods = sorted((getattr(r, "methods", None) or set()) - {"HEAD", "OPTIONS"})
    if getattr(r, "path", "").startswith("/api") and methods:
        print(",".join(methods), r.path)
PY
```

For full request and response schemas, start the stack and read the generated OpenAPI
document at `http://localhost:8080/openapi.json`.
