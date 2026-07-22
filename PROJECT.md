# Project: Agentic Growth Intelligence - Testing Phase
# Scope: Comprehensive Test Suite

## Architecture
The application consists of a FastAPI backend (with LangGraph and Pydantic AI for workflows) and a React frontend. We need to implement unit tests, end-to-end scenarios, and golden evaluations.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Synthetic Dataset & Knowledge Indexing | R1: Complete synthetic dataset for "Anka Endüstriyel Otomasyon A.Ş." in `mock_data/` | none | DONE |
| 2 | End-to-End Workflow Execution | R2: Webhook event (`POST /api/webhooks/src-crm-001`), trigger matching, StateGraph execution, 7 agent nodes, evidence grounding (`ev_...`), human approval candidate, OKF patch proposal | M1 | IN_PROGRESS |
| 3 | Golden Evaluation & Verification | R3: Golden evaluation suite execution (`scripts/run-golden-eval.py`), pytest suite, project checks (`scripts/project-check.ps1`) | M1-M2 | PLANNED |

## Interface Contracts
### E2E ↔ Backend
- E2E tests must be capable of standing up the backend, triggering LangGraph workflows, and verifying state transitions.

### Evaluation ↔ RAG
- Golden evaluations must use deterministic queries to check evidence locators and claim accuracy against mock_data in ChromaDB.

## Code Layout
- Backend Tests: `apps/api/tests/` (pytest)
- Frontend Tests: `apps/web/src/` or `apps/web/tests/` (vitest)
- E2E Tests: `apps/web/e2e/` (Playwright)
- Golden Evals: `scripts/` or `apps/api/tests/evals/`
