#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image="${1:-agentic-growth-intelligence-app:latest}"
output="${2:-${root}/artifacts/release}"
mkdir -p "${output}"

docker image inspect "${image}" >/dev/null
docker scout sbom "local://${image}" --format cyclonedx --output "${output}/sbom.cdx.json"
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v trivy_cache:/root/.cache \
  -v "${output}:/reports" \
  aquasec/trivy:0.71.2@sha256:f5d0e600ecda7449e2a9b272805aef698631d3bb3f3a739a750de2c6819acdc9 image \
  --skip-version-check \
  --scanners vuln,secret \
  --severity HIGH,CRITICAL \
  --ignore-unfixed \
  --exit-code 1 \
  --format json \
  --output /reports/trivy.json \
  "${image}"
echo "Release reports written to ${output}"
