#!/usr/bin/env bash
set -euo pipefail

source_dir="${1:?Usage: scripts/restore.sh <backup-directory>}"
source_dir="$(cd "${source_dir}" && pwd)"
actual_manifest="$(awk 'NF == 2 {print $2}' "${source_dir}/SHA256SUMS" | sort)"
expected_manifest="$(printf '%s\n' knowledge.tar.gz postgres.dump)"
if [[ "${actual_manifest}" != "${expected_manifest}" ]] || [[ "$(wc -l < "${source_dir}/SHA256SUMS")" -ne 2 ]]; then
  echo "Checksum manifest must contain exactly the two expected backup files." >&2
  exit 1
fi
(cd "${source_dir}" && sha256sum --strict -c SHA256SUMS)

if tar -tzf "${source_dir}/knowledge.tar.gz" | grep -Eq '(^/|(^|/)\.\.(/|$))'; then
  echo "Unsafe path detected in knowledge archive." >&2
  exit 1
fi
if tar -tvzf "${source_dir}/knowledge.tar.gz" | awk '$1 !~ /^[d-]/ {found=1} END {exit !found}'; then
  echo "Symlink or special entry detected in knowledge archive." >&2
  exit 1
fi

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
docker cp "${source_dir}/postgres.dump" "${postgres_id}:/tmp/agi-postgres.dump"
docker compose exec -T postgres sh -c 'pg_restore --clean --if-exists -U "$POSTGRES_USER" -d "$POSTGRES_DB" /tmp/agi-postgres.dump'
docker compose exec -T postgres rm -f /tmp/agi-postgres.dump
docker run --rm \
  -v "${knowledge_volume}:/knowledge" \
  -v "${source_dir}:/backup:ro" \
  alpine:3.22@sha256:14358309a308569c32bdc37e2e0e9694be33a9d99e68afb0f5ff33cc1f695dce sh -c 'find /knowledge -mindepth 1 -maxdepth 1 -exec rm -rf -- {} + && tar -xzf /backup/knowledge.tar.gz -C /knowledge'
trap - EXIT
restore_app
echo "Restore completed and the app service was restarted."
