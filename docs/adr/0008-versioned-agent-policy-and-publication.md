# ADR-0008: Versioned agent definitions with immutable control-plane policy

## Status

Accepted — 15 July 2026

## Decision

Administrators may create, clone, edit, and publish typed agent definitions through the Agent
Registry. Published versions are immutable and a later edit must be created by cloning the latest
version. Agent IDs and version numbers are server-controlled lineage: a new ID starts at version 1
and an existing ID can receive a new version only through the clone operation.

The editable agent instruction is versioned, but it is not the complete system policy. The model
gateway always appends an immutable control-plane policy after the editable text. That policy treats
documents, connector payloads, evidence excerpts, and retrieval results as untrusted data; denies
capability expansion and external actions; forbids using model output as evidence; and limits cited
evidence IDs to those supplied by the runtime. An editable prompt cannot remove or override these
rules.

Agent contracts remain code-constrained: model profile, typed output, capability IDs, data
classification, risk, timeout, and token budget must come from bounded allowlists. Workflow
publication resolves every referenced agent version, verifies output compatibility and model-profile
availability, and fails closed when a required built-in diagnostic role is missing.
The built-in Growth Diagnostic advances to version 3 and pins the exact four agent versions in its
node configuration. Historical unpinned version 2 remains identifiable but is not the default.

## Consequences

The web console can manage real agent versions without making prompts or workflow JSON an escape
hatch around product policy. Full prompt detail is restricted to administrators; summaries remain
available to authenticated operators. Prompt, schema, policy, capability, or model-mapping changes
invalidate previous model qualification and require the golden evaluation to be rerun.
Qualification is valid only when it executes a profile-pinned published persistent workflow and its
content-safe evidence binds exact agent versions, policy revision, and effective-prompt hashes.
