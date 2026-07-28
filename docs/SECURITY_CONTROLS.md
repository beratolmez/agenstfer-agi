# Security Controls

Maps each control in [THREAT_MODEL.md](./THREAT_MODEL.md) to the code that enforces it and
the test that proves it. A control with no test is a claim, not a control — those are marked
**untested** and carry a roadmap reference.

Last verified 28 July 2026 against `f5ba673` plus ADR-0028.

---

## Identity and session

| Control | Enforced by | Proven by |
|---|---|---|
| First admin requires the one-time bootstrap token, compared with `hmac.compare_digest` | `security.py:89-93` | `test_platform_foundation.py` |
| Only one bootstrap admin can ever be created | `security.py:90-91` | `test_platform_foundation.py` |
| Passwords hashed with Argon2 | `security.py:97` | `test_platform_foundation.py` |
| Session cookie `same_site=strict`, `https_only` in production | `main.py:149-156` | `test_platform_foundation.py` |
| CSRF token required on state-changing `/api` requests | `http_security.py:51-63` | `test_platform_foundation.py` |
| `AGI_DEMO_NO_AUTH` rejected in production | `config.py:73-74` | `test_platform_foundation.py` |
| Production refuses default secrets and requires mounted secret files | `config.py:64-82` | `test_platform_foundation.py` |

**Gap:** roles are flat — `require_role("admin")` matches the literal role with no hierarchy
(`security.py:176`). An `analyst`-only user cannot complete the Dashboard's first-diagnostic
flow because publication requires `admin` (`main.py:2103`). Roadmap: P4.

---

## Data classification boundary

| Control | Enforced by | Proven by |
|---|---|---|
| `confidential` / `restricted` content never reaches a cloud model | `agents/runtime.py:78-85` | `test_security_controls.py` |
| Contact identifiers redacted before cloud prompts | `agents/runtime.py` (`redact_identifiers`) | `test_security_controls.py` |
| Cloud reads of confidential evidence rejected at the tool boundary | `agents/runtime.py:129-131` | `test_security_controls.py` |
| Confidential aggregates blocked | — | `test_security_controls.py` |
| `ExecutionContext` privacy boundary validation | `context.py:29-33` | `test_execution_context.py` |

---

## Model gateway

| Control | Enforced by | Proven by |
|---|---|---|
| Cloud models require explicit opt-in plus provider and key; fails closed at import | `config.py:60-63` | `test_model_gateway.py`, `test_cloud_providers.py` |
| Only code-defined model profiles are resolvable | `model_gateway.py:85-108` | `test_model_gateway.py` |
| Workflow publication restricts model profiles to the allowlist | `registry_service.py:242` | `test_workflow_compatibility.py` |
| Egress restricted to four approved providers; `deny all` otherwise | `infra/egress/squid.conf` | `test_model_gateway.py:195` |
| Provider retries disabled so one run cannot exhaust a daily quota | `model_gateway.py` (`HttpRetryOptions(attempts=1)`, `max_retries=0`) | `test_model_gateway.py` |
| Production rejects an API key supplied in the request payload | `main.py:450-463` | `test_cloud_providers.py` |

---

## Prompt and tool boundary

| Control | Enforced by | Proven by |
|---|---|---|
| Control-plane policy cannot be overridden by an agent prompt | `model_gateway.py:35-49` | `test_security_controls.py` |
| Documents and connector values treated as data, never instructions | `model_gateway.py:35-40` | `test_security_controls.py` |
| Agent tools come from a code-defined allowlist; `planned` capabilities are never injected | `agents/runtime.py:184-207` | `test_dynamic_skills.py` |
| Workflow node scope can only narrow a published spec, never widen it | `agents/runtime.py:196-197`, `registry_service.py:231-240` | `test_dynamic_skills.py` |
| Invalid tool arguments produce bounded rejections rather than raw errors | `agents/runtime.py:134-143` | `test_model_assisted_diagnostic.py` |
| Arbitrary MCP URLs rejected as execution authority | `mcp.py:34-36` | `test_mcp_gateway.py`, `test_silent_failure_regressions.py` |

**Gap:** no node in the shipped workflow sets `capabilities`, so narrowing is implemented but
inactive (`workflow/default.py`). Roadmap: T5.

---

## Evidence integrity

| Control | Enforced by | Proven by |
|---|---|---|
| Raw snapshots immutable and content-addressed | `ingestion/raw_vault.py`, `ingestion/service.py:171-197` | `test_ingestion_persistence.py`, `test_connectors_runtime.py` |
| Excerpt hash re-verified against the snapshot on every read | `ingestion/service.py:328-329` | `test_ingestion_persistence.py` |
| Deterministic metric receipts bind aggregates to source evidence via digest | `domain/metrics.py:85-125`, `ingestion/service.py:298-303` | `test_model_assisted_diagnostic.py` |
| A rejected deterministic claim fails the run and creates no OKF candidate | `diagnostics/service.py:405-456` | `test_model_assisted_diagnostic.py` |
| A rejected narrative claim is withheld and reported, never published as evidence | `diagnostics/service.py:405-456`, `domain/computed_diagnostic.py` | `test_model_assisted_diagnostic.py` |
| Evidence reviewer rejects incomplete or duplicate batch decisions | `diagnostics/service.py:197-198` | `test_model_assisted_diagnostic.py` |
| Report paths confined to `reports/*.md` | `workflow/persistent_runtime.py:406-415` | `test_langgraph_default_workflow.py` |

---

## Knowledge lifecycle

| Control | Enforced by | Proven by |
|---|---|---|
| Candidates cannot alter the active bundle without an authenticated approval | `okf/lifecycle.py` | `test_okf_lifecycle.py` |
| OKF import blocks path traversal and symlinks | `okf/` import path | `test_okf.py` |
| Backup archives rejected on unsafe paths or symlinks | `scripts/restore.sh:14-21` | **untested** (shell) |

---

## Workflow governance

| Control | Enforced by | Proven by |
|---|---|---|
| Published agent and workflow versions immutable; new versions only by cloning | `registry_service.py:117-129`, `:322-331` | `test_workflow_platform.py` |
| Runs only start from a published version | `persistent_runtime.py:654-655` | `test_workflow_compatibility.py` |
| Agent versions pinned at publish and frozen again at run start | `registry_service.py:249-251`, `persistent_runtime.py:296-300` | `test_workflow_platform.py`, `test_langgraph_default_workflow.py` |
| Graph validation: single trigger, exactly one approval, approval after all report outputs, acyclic, reachable | `workflow/validator.py:17-173` | `test_workflow.py`, `test_workflow_templates.py` |
| Condition fields restricted to alphanumerics to block injection | `workflow/validator.py:41-56` | `test_workflow.py` |
| Approval decisions serialised with `SELECT … FOR UPDATE` + idempotency constraint | `persistent_runtime.py:719-732`, `db.py:280-281` | `test_workflow_platform.py` |
| Webhook events deduplicated by idempotency key before dispatch | `workflow/events.py:21-32` | `test_event_dispatch.py` |
| Scheduler survives a failing tick instead of dying silently | `workflow/scheduler.py` | `test_silent_failure_regressions.py` |
| A failed run records its error rather than staying `running` | `persistent_runtime.py:578` | `test_silent_failure_regressions.py` |

**Gap:** the published `definition` is rewritten at publish with no content hash or
signature, so integrity cannot be audited after the fact (`registry_service.py:279`).
Roadmap: SB-8.

---

## Observability boundary

| Control | Enforced by | Proven by |
|---|---|---|
| Telemetry carries method, route, status and request id only — never prompts, evidence or secrets | `observability.py:41-86` | **untested** |
| Error messages redact API keys and bearer tokens | `logging_utils.py:13-24` | `test_observability_blk06.py` |
| Error details are content-safe and structured | `logging_utils.py:27-100` | `test_observability_blk06.py` |

---

## Network boundary

| Control | Enforced by | Proven by |
|---|---|---|
| Application container has no direct internet route; `core` is `internal: true` | `docker-compose.yml` | `scripts/verify-no-egress.*` |
| All outbound model traffic passes the allowlisted proxy | `docker-compose.yml` (`HTTP(S)_PROXY`), `infra/egress/squid.conf` | `test_model_gateway.py:195` |
| Container runs as non-root (uid 10001) on digest-pinned images | `Dockerfile` | **untested** |

**Gaps:**
- `scripts/verify-no-egress.*` proves the Squid allowlist works, not that the network is
  isolated: `urllib` honours `HTTPS_PROXY`, so the 403 it observes comes from the proxy. A
  genuine isolation check must clear the proxy variables first.
- Postgres 5432 and Ollama 11434 are published to the host even though `core` is internal
  (`docker-compose.yml:53-54,98-99`). Roadmap: R6.

---

## Not covered

Out of scope for this matrix and not yet performed: penetration testing, dependency CVE
scanning beyond `scripts/release-scan.*`, load and denial-of-service behaviour, and any
review of the unreferenced `infra/kubernetes` and `infra/aws/terraform` manifests.
