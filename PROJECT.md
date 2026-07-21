# Project: Agentic Growth Intelligence - Testing Phase
# Scope: Comprehensive Test Suite

## Architecture
The application consists of a FastAPI backend (with LangGraph and Pydantic AI for workflows) and a React frontend. We need to implement unit tests, end-to-end scenarios, and golden evaluations.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Unit Tests | FastAPI backend API/utilities and React UI components | none | DONE |
| 2 | E2E Scenarios | LangGraph workflows, mock_data ingestion/retrieval via Playwright/pytest | M1 | DONE |
| 3 | Golden Evaluation | Automated evaluation script for RAG and AI checking ChromaDB | none | DONE |
| 4 | Architecture & Doc Alignment | Unify architecture diagrams, docs, and agentic business nodes | M1-M3 | IN_PROGRESS |

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
