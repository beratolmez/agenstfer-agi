# ADR 0018: Docker Network Egress Routing and Setup Completion Infinite Loop Resolution

## Status

Accepted

## Context

Diagnostic analysis of Docker container execution and the Setup Wizard onboarding flow identified two critical operational issues:
1. **Docker Container Outbound API Key Failures**: In `docker-compose.yml`, the `app` container was attached only to the `core` network (`internal: true`), isolating it from external internet access. When invoking cloud LLM provider APIs (Gemini, Groq, Mistral, OpenRouter), outgoing requests failed inside Docker containers despite succeeding in local development.
2. **Dashboard Navigation Infinite Loop**: In `SetupWizard.tsx`, finishing step 5 submitted `completed_steps: [1, 2, 3, 4, 5]`. Backend `/api/setup/progress` strictly checked `completed == list(range(10))`, raising HTTP 409 Conflict. Because the error was caught silently, `InstallationState` in DB was never updated to `status: "completed"`. On navigation to `"dashboard"`, `App.tsx` re-evaluated `!setup_completed`, forcing the user back into `SetupWizard` in an infinite loop.

## Decisions

1. **Docker Container Network Egress Proxy Integration**:
   - Attached `app` service to both `core` and `egress` networks in `docker-compose.yml`.
   - Configured `HTTPS_PROXY: http://egress-gateway:3128` and `HTTP_PROXY: http://egress-gateway:3128` on `app` with `NO_PROXY` set for internal services (`postgres`, `ollama`, `qmd`, `egress-gateway`, `web-proxy`).
   - Ensured `egress-gateway` runs as the allowlisted proxy gateway for cloud model provider domains (`.generativelanguage.googleapis.com`, `.api.groq.com`, `.api.mistral.ai`, `.openrouter.ai`).

2. **Setup Completion Step Resolution and App State Refresh**:
   - Updated `/api/setup/progress` endpoint in `main.py` so that when `payload.status == "completed"`, `completed` is automatically set to `list(range(10))`, updating `InstallationState` in DB to `status: "completed"` without raising HTTP 409.
   - Updated `SetupWizard.tsx` to send `current_step: 9` and `completed_steps: Array.from({ length: 10 }, (_, i) => i)`.
   - Updated `App.tsx` `onComplete` handler to refresh `setupStatus` from backend (`api.setupStatus().then(setSetupStatus)`), ensuring `setup_completed` updates to `true` in React state immediately before navigating to `"dashboard"`.

## Consequences

- Restores cloud LLM API connectivity inside Docker containers while preserving strict egress allowlisting via `egress-gateway`.
- Eliminates HTTP 409 Conflict on setup completion.
- Resolves the Dashboard navigation infinite loop, enabling seamless onboarding transition to the main application shell.
