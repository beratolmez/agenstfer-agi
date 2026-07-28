#!/usr/bin/env bash
set -euo pipefail

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
target="${1:-./backups/${timestamp}}"
mkdir -p "${target}"
target="$(cd "${target}" && pwd)"

postgres_id="$(docker compose ps -q postgres)"
app_id="$(docker compose ps -q app)"
if [[ -z "${postgres_id}" || -z "${app_id}" ]]; then
  echo "The postgres and app services must be running." >&2
  exit 1
fi

knowledge_volume="$(docker inspect "${app_id}" --format '{{range .Mounts}}{{if eq .Destination "/data/knowledge"}}{{.Name}}{{end}}{{end}}')"
if [[ -z "${knowledge_volume}" ]]; then
  echo "Could not resolve the mounted knowledge volume." >&2
  exit 1
fi

restore_app() {
  docker start "${app_id}" >/dev/null
  for _ in $(seq 1 60); do
    status="$(docker inspect "${app_id}" --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}')"
    [[ "${status}" == "healthy" || "${status}" == "running" ]] && return 0
    [[ "${status}" == "unhealthy" || "${status}" == "exited" || "${status}" == "dead" ]] && return 1
    sleep 2
  done
  return 1
}
docker compose stop app
trap restore_app EXIT
docker compose exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/agi-postgres.dump'
docker cp "${postgres_id}:/tmp/agi-postgres.dump" "${target}/postgres.dump"
docker compose exec -T postgres rm -f /tmp/agi-postgres.dump
docker run --rm \
  -v "${knowledge_volume}:/knowledge:ro" \
  -v "${target}:/backup" \
  alpine:3.22@sha256:14358309a308569c32bdc37e2e0e9694be33a9d99e68afb0f5ff33cc1f695dce tar -czf /backup/knowledge.tar.gz -C /knowledge .
(cd "${target}" && sha256sum postgres.dump knowledge.tar.gz > SHA256SUMS)
trap - EXIT
restore_app
echo "Backup created at ${target}"
