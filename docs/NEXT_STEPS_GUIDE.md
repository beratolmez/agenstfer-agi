# Daily Development Guide

1. Read `IMPLEMENTATION_STATUS.md`, then the architecture and active implementation phase.
2. Work only on the active phase or a prerequisite defect.
3. Start from data, evidence, and deterministic metrics before changing prompts.
4. Treat all imported content as untrusted data.
5. Keep external connectors read-only and separate read/write permissions in future designs.
6. Never interpret model wording or a score as probability/confidence.
7. Preserve unknown OKF types and fields; isolate OKF version changes in the adapter.
8. Add evidence locators before calling a generated claim complete.
9. Run the golden evaluation after model, prompt, tool, retrieval, mapping, or scoring changes.
10. Record durable architecture/security choices in an ADR and update status with evidence.

Before ending a change, run `scripts/project-check.ps1` on Windows or `scripts/project-check.sh` on Linux. Add the phase-specific database, workflow-restart, model-evaluation, browser, or security checks required by root `AGENTS.md`.

## When a real company arrives

- Classify its data and confirm retention/privacy/consent requirements with the appropriate legal/security owners.
- Discover its actual CRM/ERP before selecting the first connector.
- Benchmark local hardware and qualified model profiles with representative but approved data.
- Update the threat model, backup policy, source mappings, and golden evaluation.
- Start with a read-only pilot and compare recommendations with human decisions.
- Do not enable controlled write actions until separate policy, approval, consent, and rollback work is accepted.

