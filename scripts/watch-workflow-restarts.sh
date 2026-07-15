#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage: scripts/watch-workflow-restarts.sh --output PATH --approval-ready-file PATH
       [--workflow-id release-growth-diagnostic] [--timeout-seconds 7200]

Waits for a real agent step, restarts the exact app container, waits for the same run to enter
approval, restarts the same container again, and records content-safe restart evidence.
EOF
}

workflow_id="release-growth-diagnostic"
output=""
approval_ready_file=""
timeout_seconds="7200"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --workflow-id) workflow_id="${2:-}"; shift 2 ;;
    --output) output="${2:-}"; shift 2 ;;
    --approval-ready-file) approval_ready_file="${2:-}"; shift 2 ;;
    --timeout-seconds) timeout_seconds="${2:-}"; shift 2 ;;
    *) usage; exit 2 ;;
  esac
done

if [[ ! "${workflow_id}" =~ ^[a-z0-9][a-z0-9-]{0,79}$ ]] \
  || [[ -z "${output}" || -z "${approval_ready_file}" ]] \
  || [[ ! "${timeout_seconds}" =~ ^[0-9]+$ ]] \
  || (( timeout_seconds < 60 || timeout_seconds > 21600 )); then
  usage
  exit 2
fi
if [[ "${output}" == "${approval_ready_file}" || -L "${output}" || -L "${approval_ready_file}" ]]; then
  echo "Evidence and coordination paths must be distinct, non-symlink files." >&2
  exit 2
fi

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${root}"
mkdir -p "$(dirname "${output}")" "$(dirname "${approval_ready_file}")"
rm -f "${output}" "${approval_ready_file}"

compose=(docker compose -f docker-compose.yml -f docker-compose.production.yml)
app_id="$("${compose[@]}" ps -q app)"
postgres_id="$("${compose[@]}" ps -q postgres)"
if [[ -z "${app_id}" || -z "${postgres_id}" ]]; then
  echo "The release app and postgres containers must be running." >&2
  exit 1
fi

restart_records="$(mktemp)"
status="failed"
failure_code="watchdog_incomplete"
run_id=""
agent_step=""
final_run_status="unknown"
started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
deadline=$((SECONDS + timeout_seconds))

write_evidence() {
  python3 - \
    "${restart_records}" "${output}" "${status}" "${failure_code}" \
    "${workflow_id}" "${run_id}" "${agent_step}" "${final_run_status}" "${started_at}" <<'PY'
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

records_path, output_path, status, failure_code, workflow_id, run_id, agent_step, final_status, started_at = sys.argv[1:]
fields = [
    "stage",
    "run_id",
    "container_id_before",
    "container_id_after",
    "container_started_at_before",
    "container_started_at_after",
    "healthy_at",
    "health_after",
    "run_status_before",
    "step_status_before",
    "approval_status_before",
]
restarts = []
for line in Path(records_path).read_text(encoding="utf-8").splitlines():
    values = line.split("\t")
    if len(values) == len(fields):
        restarts.append(dict(zip(fields, values, strict=True)))
payload = {
    "schema": "agi-workflow-restart-evidence-v1",
    "status": status,
    "failure_code": failure_code or None,
    "workflow_id": workflow_id,
    "run_id": run_id or None,
    "agent_step": agent_step or None,
    "final_run_status": final_status,
    "started_at": started_at,
    "finished_at": datetime.now(timezone.utc).isoformat(),
    "restarts": restarts,
    "content_policy": "No prompts, source bodies, evidence excerpts, credentials, or provider keys.",
}
target = Path(output_path)
temporary = target.with_name(target.name + ".tmp")
temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, target)
PY
}

on_exit() {
  local code=$?
  trap - EXIT
  write_evidence || true
  rm -f "${restart_records}"
  exit "${code}"
}
trap on_exit EXIT

fail() {
  failure_code="$1"
  echo "Restart watchdog failed: ${failure_code}" >&2
  return 1
}

sql_query() {
  local query="$1"
  docker exec "${postgres_id}" sh -c \
    'psql -v ON_ERROR_STOP=1 -At -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$1"' \
    sh "${query}"
}

container_started_at() {
  docker inspect "${app_id}" --format '{{.State.StartedAt}}'
}

wait_healthy() {
  local health
  while (( SECONDS < deadline )); do
    if [[ "$(docker inspect "${app_id}" --format '{{.Id}}' 2>/dev/null || true)" != "${app_id}" ]]; then
      fail "app_container_id_changed"
      return 1
    fi
    health="$(docker inspect "${app_id}" --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}')"
    [[ "${health}" == "healthy" ]] && return 0
    [[ "${health}" == "unhealthy" || "${health}" == "exited" || "${health}" == "dead" ]] \
      && fail "app_failed_after_restart" && return 1
    sleep 1
  done
  fail "app_health_timeout"
}

agent_query="
SELECT wr.id || '|' || wr.current_step || '|' || wsr.status
FROM workflow_runs wr
JOIN workflow_step_runs wsr
  ON wsr.run_id = wr.id AND wsr.step_id = wr.current_step
WHERE wr.workflow_id = '${workflow_id}'
  AND wr.status = 'running'
  AND wr.current_step IN ('company_agent', 'growth_agent', 'review', 'curator')
  AND wsr.status = 'running'
ORDER BY wr.started_at DESC
LIMIT 1;"

agent_record=""
while (( SECONDS < deadline )); do
  if ! agent_record="$(sql_query "${agent_query}")"; then
    fail "database_query_failed"
    exit 1
  fi
  [[ -n "${agent_record}" ]] && break
  sleep 1
done
[[ -n "${agent_record}" ]] || { fail "agent_step_timeout"; exit 1; }
IFS='|' read -r run_id agent_step step_status <<<"${agent_record}"
if [[ ! "${run_id}" =~ ^[0-9a-f-]{36}$ || "${step_status}" != "running" ]]; then
  fail "invalid_agent_checkpoint"
  exit 1
fi

first_before="$(container_started_at)"
docker restart "${app_id}" >/dev/null
wait_healthy
first_after="$(container_started_at)"
first_healthy="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
  "agent_execution" "${run_id}" "${app_id}" "${app_id}" "${first_before}" "${first_after}" \
  "${first_healthy}" "healthy" "running" "running" "" >> "${restart_records}"

approval_status=""
while (( SECONDS < deadline )); do
  if ! run_record="$(sql_query "
SELECT wr.status || '|' || COALESCE(wr.current_step, '') || '|' || COALESCE(ar.status, '')
FROM workflow_runs wr
LEFT JOIN approval_requests ar
  ON ar.run_id = wr.id AND ar.status IN ('pending', 'decision_submitted')
WHERE wr.id = '${run_id}'
LIMIT 1;")"; then
    fail "database_query_failed"
    exit 1
  fi
  IFS='|' read -r run_status current_step approval_status <<<"${run_record}"
  final_run_status="${run_status:-unknown}"
  if [[ "${run_status}" == "awaiting_approval" && "${approval_status}" == "pending" ]]; then
    break
  fi
  if [[ "${run_status}" =~ ^(failed|rejected|expired|cancelled)$ ]]; then
    fail "run_terminated_before_approval"
    exit 1
  fi
  sleep 1
done
if [[ "${final_run_status}" != "awaiting_approval" || "${approval_status}" != "pending" ]]; then
  fail "approval_wait_timeout"
  exit 1
fi

# Give DBOS.recv time to persist the durable wait before the process is interrupted.
sleep 2
second_before="$(container_started_at)"
docker restart "${app_id}" >/dev/null
wait_healthy
second_after="$(container_started_at)"
second_healthy="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
  "approval_wait" "${run_id}" "${app_id}" "${app_id}" "${second_before}" "${second_after}" \
  "${second_healthy}" "healthy" "awaiting_approval" "awaiting_approval" "pending" \
  >> "${restart_records}"
printf '%s\n' "${run_id}" > "${approval_ready_file}"

while (( SECONDS < deadline )); do
  if ! final_run_status="$(sql_query "SELECT status FROM workflow_runs WHERE id = '${run_id}';")"; then
    fail "database_query_failed"
    exit 1
  fi
  [[ "${final_run_status}" == "completed" ]] && break
  if [[ "${final_run_status}" =~ ^(failed|rejected|expired|cancelled)$ ]]; then
    fail "run_terminated_after_approval_restart"
    exit 1
  fi
  sleep 1
done
[[ "${final_run_status}" == "completed" ]] || { fail "completion_timeout"; exit 1; }

status="passed"
failure_code=""
echo "Restart evidence captured for workflow run ${run_id}."
