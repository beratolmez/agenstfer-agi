# Infrastructure

## Active deployment

Docker Compose is the shipped deployment model (ADR-0009: isolated, customer-private
installation). Everything the running product needs lives here:

| Path | Used by | Purpose |
|---|---|---|
| `proxy/nginx.conf` | `docker-compose.yml` (`web-proxy`) | Reverse proxy, gzip, WebSocket upgrade, static asset caching |
| `egress/squid.conf` | `docker-compose.yml` (`egress-gateway`) | Allowlisted egress; only the four approved model providers, `deny all` otherwise |
| `qmd/` | `docker-compose.yml` (`qmd`, `profiles: [search]`) | Retrieval service for OKF bundle search. Not started by default |

## Not wired up

`kubernetes/` and `aws/terraform/` are a second deployment definition that no script,
compose file or CI job references, and that has not been kept in sync with the Compose
topology. They are retained as a starting point for a future managed-hosting option, not
as a supported path.

Before using either, reconcile them against `docker-compose.yml` and
`docker-compose.production.yml` first — in particular the secret mounts, the egress
allowlist and the `core` network isolation, none of which are represented there. See
`docs/REMEDIATION_ROADMAP.md` for the open decision on the deployment target.

`aws/docker-compose.prod.yml` is likewise unreferenced; ADR-0024 describes its intent.
