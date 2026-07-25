# ADR-0020: Audit Report Runde 2 High Priority Fixes

## Status
Accepted

## Context
During the technical audit documented in `docs/AUDIT_RAPORT.md`, 12 high-priority issues were identified in UX, API contracts, environment configuration, and documentation accuracy:
1. **Bulgu 4.3**: Vite dev server proxy target pointed to port `8000` while FastAPI uvicorn server runs on port `8080`.
2. **Bulgu 5.1 & Bulgu 5.3**: `.env.example` contained misleading non-prefixed `GEMINI_*` keys and deprecated `AGI_ENABLE_DBOS` variables. `config.py` contained unreferenced `enable_dbos` field.
3. **Bulgu 3.8**: `SetupWizard.tsx` onboarding setup progress persistence omitted `model_profile`, `source_mode`, and `locale` fields.
4. **Bulgu 3.5**: Frontend API contract in `api.ts` omitted `candidate_id` from `decideCandidate` response payload type.
5. **Bulgu 1.2 & Bulgu 1.1**: `README.md` contained dead links to non-existent documentation files (`ARCHITECTURE_CONTEXT.md`, `ENGINEERING_FOCUS_ROADMAP.md`, `MVP_IMPLEMENTATION_PLAN.md`, `NEXT_STEPS_GUIDE.md`).
6. **Bulgu 1.4**: `OPERATIONS_RUNBOOK.md` referenced non-existent `.secrets/gemini_api_key` instead of `.secrets/cloud_model_api_key`.
7. **Bulgu 2.1**: `IMPLEMENTATION_STATUS.md` claimed "Tailwind CSS" despite UI being implemented in Vanilla CSS.
8. **Bulgu 2.5**: `NEW_ARCHITECTURE_PLAN.md` contained outdated multi-service specifications without deprecation warning.
9. **Bulgu 3.2**: `SetupWizard.tsx` swallowed background progress auto-save errors.
10. **Bulgu 2.3**: Verification confirmed ADR-0017 cloud probe non-silent error handling is enforced.

## Decision
1. Update `apps/web/vite.config.ts` proxy target port to `http://localhost:8080`.
2. Clean `.env.example` to remove `GEMINI_*` and `AGI_ENABLE_DBOS`, and document `AGI_CLOUD_*` prefixed settings. Remove `enable_dbos` from `apps/api/agi_server/config.py`.
3. Include `model_profile`, `source_mode`, and `locale` in `saveSetupProgress` calls in `SetupWizard.tsx`.
4. Update `api.ts` `decideCandidate` response type to include `candidate_id: string`.
5. Remove broken documentation links from `README.md` and redirect architecture reference to `docs/SYSTEM_ARCHITECTURE.md`.
6. Fix secret file path in `docs/OPERATIONS_RUNBOOK.md` to `.secrets/cloud_model_api_key`.
7. Update `docs/IMPLEMENTATION_STATUS.md` to specify "Vanilla CSS".
8. Add deprecation warning banner to `docs/NEW_ARCHITECTURE_PLAN.md`.
9. Log background save errors in `SetupWizard.tsx`.

## Consequences
- Local development Vite dev server proxies API calls cleanly to port 8080.
- Environment variables and config schemas are clean, consistent, and correctly prefixed with `AGI_`.
- Onboarding progress configuration accurately persists model profile, source mode, and locale choices.
- Frontend TypeScript types match full backend API response structures.
- Documentation links in README, Runbook, and Status docs are valid and authoritative.
