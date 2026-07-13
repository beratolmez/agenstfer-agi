# ADR-0005: Ingress and network boundaries

## Status

Accepted — 13 July 2026

## Decision

Only `web-proxy` publishes a host port. FastAPI, PostgreSQL, Ollama, and qmd stay on the internal `core` network. Nginx forwards browser traffic to the application and preserves forwarding headers. Optional cloud traffic leaves only through an allowlisted egress network. Production TLS terminates at a documented reverse proxy or the installation's approved ingress.

## Consequences

The browser has one stable origin and internal services are not directly host-accessible. Health checks must distinguish process reachability from dependency readiness. A production deployment must reject untrusted forwarding headers unless they originate from the ingress proxy.

