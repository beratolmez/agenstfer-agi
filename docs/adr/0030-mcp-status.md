# ADR-0030: MCP Status — Finish the Transport or Reclassify

- **Status:** Accepted — Option A
- **Date:** 28 July 2026
- **Amends:** ADR-0016 Phase 7, which recorded the MCP gateway as delivered
- **Blocks:** T6 in `docs/REMEDIATION_ROADMAP.md`

## Context

`IMPLEMENTATION_STATUS.md` described the MCP client gateway as an active capability. It is
not. What exists is a policy layer with no transport underneath it:

**Real and tested** (`mcp.py:33-70`, six tests in `test_mcp_gateway.py`): rejection of
arbitrary user-supplied URLs, approval and active-status checks, read-only enforcement,
data-classification fail-closed for cloud profiles, and a tool allowlist.

**Not real:**
- `invoke_tool` returns a fixed dictionary when no transport is injected (`mcp.py:76-80`).
  There is no JSON-RPC, no stdio, no SSE, no `initialize` handshake.
- `MCPProfile.transport_type` is never read; nor are `timeout_seconds` or `configuration`.
- No production code path constructs an `MCPGateway` — the only references are the class
  definition and the tests.
- No `MCPProfile` row is ever created. `ensure_platform_registry` seeds agents,
  capabilities and workflows only, and there is no migration or script that seeds profiles.
  **The table is always empty in production.**
- The `mcp.query` and `mcp.read_resource` capabilities are advertised as `available` but map
  to the `read_evidence` handler (`capabilities.py:95,103`) and `for_spec` has no branch that
  binds them (`agents/runtime.py:199-206`). They are dead twice over.
- `pyproject.toml` declares no MCP dependency. One is present transitively via
  `pydantic-ai`, but nothing in `apps/api` imports it.

Only the one non-stub piece works: `/api/sources/test-mcp` does attempt a real
`tools/list` JSON-RPC POST (`main.py:1568-1587`), though without the `initialize` handshake,
session header or SSE `Accept` that a streamable-HTTP MCP server requires. It also returns a
hardcoded `protocol_version` of `"2024-11-05"` rather than negotiating one.

## Options

**A. Reclassify as target specification.** Keep the policy layer and its tests as the
governance skeleton, mark MCP as not implemented across the documents, remove `mcp.query`
and `mcp.read_resource` from the capability registry and the Workflow Editor so they stop
appearing as selectable skills, and stop `/api/sources/test-mcp` from reporting a negotiated
protocol version it never negotiated.
*Cost:* low. *Consequence:* the connector story in the PRD (§6.8) has no MCP path until this
is revisited.

**B. Implement the transport.** Add a real MCP client — `pydantic-ai` already ships MCP
support transitively, so this can plug into the existing agent toolset rather than being
written from scratch. Requires: profile seeding and CRUD, `transport_type` dispatch,
handshake and session handling, timeout enforcement, and routing tool calls through
`MCPGateway` so the existing allowlist actually gates them.
*Cost:* high, and it opens a new external-execution surface that the threat model must cover.
*Consequence:* delivers the connector extensibility the PRD describes.

## Recommendation

**A now, B when a customer integration actually requires it.** The policy layer is the hard
part and it is already built and tested; it will still be there when a transport is added.
Meanwhile advertising two dead capabilities in the Workflow Editor is exactly the kind of
overstatement this codebase has been paying for elsewhere.

If B is chosen, it should not begin before D1 (multi-tenancy) is settled — an MCP server
reachable from an agent is a data-egress path, and its boundary depends on whether the
deployment is single-tenant.

## Consequences of not deciding

Administrators can assign `mcp.query` to an agent through the UI today and get silent
no-ops, with nothing in the interface indicating the capability does nothing.

## Decision taken

**Option A, approved 29 July 2026.** MCP is reclassified as a target specification. The
policy layer and its tests stay as the governance skeleton; the two dead `mcp.*`
capabilities are removed from the registry so they stop appearing as assignable skills,
and the documents stop describing MCP as active.

The tools the product actually needs — web search, and later messaging — are delivered as
native capabilities, which cost three files rather than a transport, handshake, session
layer and a new external-execution surface. MCP's value is a customer bringing their own
tools; it is revisited when a customer integration requires it, and not before ADR-0032
settled the tenancy boundary (it now has).
