# ADR 0017: Model Gateway Authentication Alignment and Onboarding Flow Resolution

## Status

Accepted

## Context

During diagnostic audit of model connectivity and the Setup Wizard onboarding experience, several issues were identified:
1. **Model Gateway Header Handling**: Google Gemini's OpenAI-compatible endpoint (`/v1beta/openai/`) expects `Authorization: Bearer <key>`. Setting custom `x-goog-api-key` headers on `httpx.AsyncClient` created duplicate/conflicting authentication headers for Pydantic AI's `OpenAIChatModel`.
2. **Setup Progress Configuration Schema**: Frontend `SetupWizard` passes `company_name`, `industry`, `objective`, `provider`, `model`, `model_profile`, `source_mode`, and `locale`. Backend endpoint `/api/setup/progress` restricted `allowed_keys` to a subset, causing `422 Unprocessable Entity` errors on progress saving.
3. **Onboarding Gate Enforcement**: ADR-0004 required full-screen onboarding gate enforcement before land on Dashboard shell when setup was incomplete.

## Decisions

1. **Standardized Bearer Token Authentication for Cloud Providers**:
   - In `model_gateway.py`, removed custom `x-goog-api-key` header overrides on HTTP client instances when initializing `OpenAIProvider`. Standardized Bearer token authentication across all OpenAI-compatible cloud provider endpoints (`gemini`, `groq`, `mistral`, `openrouter`).

2. **Synchronized Setup Progress Configuration Schema**:
   - Updated `/api/setup/progress` endpoint `allowed_keys` in `main.py` to allow `company_name`, `industry`, `objective`, `provider`, `model`, `model_profile`, `source_mode`, and `locale` with string length validations.

3. **Truthful Probe Error Handling and Full-Screen Onboarding Gate**:
   - In `SetupWizard.tsx`, removed silent fallback to `local-balanced` when probing cloud models, presenting exact cloud probe error feedback.
   - In `App.tsx`, enforced full-screen `SetupWizard` display when `setup_completed` is `false` or when `view === "setup"`.

## Consequences

- Resolves API key authentication header conflicts for Gemini and other OpenAI-compatible cloud providers.
- Eliminates 422 errors on setup progress persistence.
- Enforces ADR-0004 full-screen onboarding gate compliance.
