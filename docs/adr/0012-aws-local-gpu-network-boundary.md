# ADR-0012: AWS control plane and private inference boundary

## Status

Accepted for deployment design — 17 July 2026

## Context

The target architecture may place the control plane in AWS while the vendor provides and operates
the GPU server that hosts Ollama, vLLM, or another approved model server. These environments may be
separate networks. Publicly exposing a model endpoint would create an unacceptable attack surface,
and automatic local-to-cloud fallback is prohibited.

## Decision

The Model Gateway remains provider-neutral and deployment-independent. A deployment must choose one
explicit inference pattern:

1. vendor GPU service in the same private AWS/VPC boundary,
2. private AWS-to-vendor-GPU VPN or private service link, or
3. vendor-side outbound inference gateway that polls for typed jobs over authenticated HTTPS.

The inference endpoint is never public. For the first release, a dedicated GPU server per customer or
a dedicated model process/queue with strict isolation is preferred. Shared GPU execution across
customers is not an MVP assumption. The selected pattern, customer/region ownership, data route,
encryption, timeout, failure behavior, and capacity policy are recorded in the deployment manifest.
Model failure does not silently route data to another provider.

## Consequences

- AI code does not depend on VPN, queue, or cloud-specific SDK details.
- The split-private pattern requires deployment engineering for private routing or a durable job
  protocol, plus vendor GPU capacity and incident ownership.
- A first production profile should select the least operationally risky pattern approved by DevOps.
