# Engineering Focus Roadmap

Last updated: 17 July 2026

This roadmap is for the AI engineer responsible for agent, retrieval, model, and evaluation work.
You do not need to become the primary DevOps engineer, but you must understand the interfaces and
failure modes well enough to design safe AI features with the deployment team.

## Priority 1 — Evidence-first product behavior

Learn the project's business and trust model before adding new agents:

- Data classification: `public`, `internal`, `confidential`, `restricted`.
- Raw snapshot, EvidenceItem, locator, hash, and deterministic metric receipt.
- OKF 0.1 concepts, references, candidate/active Git lifecycle, and qmd fallback.
- Why model confidence is not evidence coverage.
- How every material/numerical claim resolves to immutable evidence.

Practice task: take one generated report claim and trace it from UI to EvidenceItem, raw snapshot,
locator, hash, and approved OKF revision.

## Priority 2 — Typed agent engineering

Focus on Pydantic AI and reliable model interaction:

- Pydantic schemas and strict structured output.
- Prompt boundaries: source text is untrusted data, not instructions.
- Capability-scoped tools and bounded context construction.
- Retry, timeout, cancellation, idempotency, and fail-closed behavior.
- Model profile pinning, provider differences, and structured-output probes.
- Prompt/effective-policy versioning and golden evaluation.

Practice task: change one agent output field, update its contract and tests, then run the golden
evaluation and unsupported-claim checks.

## Priority 3 — RAG and knowledge quality

Learn retrieval as a controlled evidence pipeline rather than a chat feature:

- Lexical/BM25 retrieval, chunking, metadata filters, and hybrid retrieval.
- Query scoping by company, revision, classification, and source.
- Reranking and context budgets.
- Citation resolution and evidence completeness.
- LLM Wiki/OKF curation, contradiction/staleness checks, and candidate approval.
- When embeddings help and when deterministic metrics are more trustworthy.

Practice task: compare lexical, hybrid, and reranked retrieval on a small golden question set and
measure citation correctness, not only answer similarity.

## Priority 4 — Durable workflow and agent orchestration

Learn DBOS and the project's typed workflow DSL:

- Durable steps, checkpoints, retries, pause/resume, and approval waits.
- Immutable workflow and agent versions.
- Safe conditions and typed branches.
- Idempotency keys and duplicate-run prevention.
- Artifact references instead of oversized workflow payloads.
- Why the MVP uses a deterministic four-agent pipeline instead of an agent swarm.

Practice task: restart a run during an agent step and during approval; verify the same run ID resumes
without duplicate evidence or candidate merge.

## Priority 5 — Model serving and vendor GPU operations

Because the vendor supplies the GPU servers, learn the model-serving boundary in depth:

- GPU memory, VRAM limits, quantization, context length, batching, and concurrency.
- Latency versus throughput and queueing behavior.
- Ollama and vLLM serving models behind an OpenAI-compatible private API.
- CUDA/driver/runtime compatibility at a conceptual level.
- Model download, checksum/provenance, warm-up, health checks, and rollback.
- Dedicated GPU versus isolated model process/queue per customer.
- Noisy-neighbor risk, quotas, rate limits, and per-customer capacity.
- Private service links, VPNs, outbound gateways, and why model ports are never public.

Practice task: create a benchmark sheet for each release-enabled model containing structured-output
success, latency percentiles, VRAM usage, tokens/second, timeout rate, and evidence-gate results.

You do not need to manage every VPC route, but you should be able to explain the request path:

```text
Customer installation → private Model Gateway → vendor GPU gateway → model server → typed result
```

## Priority 6 — Observability and evaluation

Learn OpenTelemetry and Langfuse for model behavior, not for storing company content:

- Traces, spans, run/step IDs, and correlation across DBOS and Pydantic AI.
- Token usage, latency, retries, structured-output failures, and model cost.
- Dataset/golden-run evaluation and regression detection.
- Prompt version and model profile comparison.
- PII redaction, content-safe metadata, retention, RBAC, and self-hosted telemetry settings.

Practice task: investigate a failed run using only trace metadata and persisted evidence IDs, without
opening prompt bodies or copying source content into logs.

## Priority 7 — Security and deployment literacy

Learn enough AWS and security to make safe design decisions:

- VPC, public/private subnets, security groups, IAM roles, KMS/secrets, and TLS termination.
- RDS, encrypted object storage, backup/restore, migration, and rollback concepts.
- Container images, SBOM, vulnerability scanning, and signed releases.
- SSRF, prompt injection, XSS, path traversal, archive bombs, and data exfiltration.
- Cloud egress allowlists and data-classification policy.

The goal is not to replace DevOps. The goal is to know which AI decisions create deployment,
security, or data-residency consequences.

## Priority 8 — Productized workflow and connector design

Learn the difference between:

- A vendor-delivered capability or connector.
- A customer-configured workflow using safe nodes.
- A future MCP adapter.
- A high-risk external write action.

First-party typed read-only connectors are the default for known CRM/ERP products. MCP can be added
behind the same policy boundary, but it must not become an unrestricted plugin system.

## Defer until the foundations pass

- Dynamic bounded worker rounds for the core diagnostic.
- Shared GPU execution across customers.
- CRM/ERP write-back.
- Voice, messaging, outreach, social automation, and autonomous actions.
- Multimodal RAG and OCR.
- Kubernetes autoscaling and event-bus redesign.

## Recommended weekly order

1. Evidence and OKF traceability.
2. Pydantic AI typed agents and evaluation.
3. RAG retrieval quality.
4. DBOS workflow reliability.
5. Vendor GPU/model serving.
6. Langfuse/OpenTelemetry evaluation.
7. AWS/security/deployment literacy.
8. Product connectors and controlled future extensions.

