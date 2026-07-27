# ADR-0023: First Diagnostic Workflow Registry Binding Synchronization Fix

## Status
Accepted

## Context
When a user initiates the first diagnostic run from the Web Console Dashboard, the application clones `builtin-growth-diagnostic` v3 into `growth-diagnostic` v1 and attempts to publish it.

During `workflow_publish` and `validate_workflow_bindings`, validation verifies that all agent node references (`company-analyst` v3, `growth-opportunity-analyst` v3, `evidence-reviewer` v3, `wiki-curator` v2) are present in the `AgentDefinitionRow` database table with `status == 'published'`. On fresh database installations or uninitialized sessions, built-in agent specifications were not automatically seeded/updated into `AgentDefinitionRow` prior to binding validation, resulting in `Workflow registry binding validation failed` errors.

## Decision
1. In `apps/api/agi_server/workflow/registry_service.py`:
   - Update `ensure_platform_registry(db)` to synchronize agent row fields (`status = 'published'`, `name = spec.name`, `definition = spec.model_dump()`) for both new and existing agent definition records.
   - Invoke `ensure_platform_registry(db)` at the start of `validate_workflow_bindings(db, workflow)`.
2. In `apps/api/agi_server/main.py`:
   - Invoke `ensure_platform_registry(db)` in `setup_progress_update` when `payload.status == 'completed'`.
   - Invoke `ensure_platform_registry(db)` in `workflow_clone` before executing `clone_workflow_version`.
   - Invoke `ensure_platform_registry(db)` in `workflow_publish` before executing `publish_workflow(db, row)`.

## Consequences
- Built-in platform agents and allowlisted capabilities are guaranteed to be seeded and published before any workflow publishing or binding validation check.
- Dashboard "İlk tanıyı çalıştır" action creates and publishes diagnostic workflow clones without encountering missing agent version errors.
- System state consistency survives database resets and fresh onboarding setups.
