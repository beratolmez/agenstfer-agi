# ADR-004: Unified 6-Step Onboarding Flow and Dynamic LLM Model Discovery

- **Status**: Approved
- **Date**: 2026-07-24
- **Authors**: Core Engineering Team

## Context

During initial deployment and user onboarding, users previously experienced separate authentication gates (Bootstrap Admin creation) and an in-dashboard setup wizard. This created UX friction where unconfigured deployments would land on empty dashboard states. Furthermore, hardcoded LLM model names required frequent codebase updates as cloud providers (Google Gemini API, Groq, Mistral) released new models.

## Decision

1. **Unified 6-Step Full-Screen Onboarding Flow**:
   - Integrate First Admin Bootstrap creation into Step 1 of a single, full-screen 6-Step Setup Wizard (`SetupWizard.tsx`).
   - Enforce a strict control plane gate in `App.tsx` preventing access to the Dashboard shell until onboarding setup is completed.

2. **Dynamic LLM Model Discovery Endpoint (`/api/models/discover`)**:
   - Introduce `POST /api/models/discover` in FastAPI.
   - When an API key is provided, dynamically query the provider's model catalog (`https://generativelanguage.googleapis.com/v1beta/models`) to list available models for that specific key.
   - Default Gemini choices to `gemini-3.6-flash` and `gemini-3.5-flash-lite`.

3. **Detailed Model Structured-Output Probe Feedback**:
   - Surface exact HTTP status details (e.g. `401 Unauthorized - Invalid API Key`, `404 Model Not Found`) in prominent UI alert cards with actionable troubleshooting hints.

## Consequences

- **Security & UX**: Complete isolation of unconfigured environments until administrator creation and model probe verification succeed.
- **Provider Resilience**: Model dropdowns automatically reflect newly accessible models for any given Gemini or Cloud provider API key without requiring frontend code changes.
