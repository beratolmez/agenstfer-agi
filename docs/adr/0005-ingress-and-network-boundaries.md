# ADR-0005: Ingress and network boundaries

## Status

Accepted — 13 July 2026

## Decision

In the default profile only `web-proxy` publishes a host port. FastAPI, PostgreSQL, Ollama, and qmd
stay on the internal `core` network. Nginx forwards browser traffic to the application and preserves
forwarding headers. Optional cloud traffic leaves only through an allowlisted egress network.
Production TLS terminates at a documented reverse proxy or the installation's approved ingress.

Amendment — 14 July 2026: the explicit `observability` profile may also publish the Jaeger v2 UI on
port 16686. Jaeger joins `core` for OTLP ingestion and `ingress` only for its UI. It is absent from the
default profile.

The one-time `docker-compose.model-download.yml` overlay is an explicit operator action. It adds
only Ollama to a temporary non-internal network while an allowlisted model is pulled. The helper
scripts always recreate Ollama on the internal-only base topology afterwards; the application and
company data services never join the download network.

## Consequences

The product browser has one stable origin and internal services are not directly host-accessible.
Operators who enable observability must protect the Jaeger UI with the same host/firewall access
policy. Health checks must distinguish process reachability from dependency readiness. A production
deployment must reject untrusted forwarding headers unless they originate from the ingress proxy.
