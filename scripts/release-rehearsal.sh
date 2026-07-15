#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage: scripts/release-rehearsal.sh --base-url https://host --admin-email EMAIL
       --model-profile local-balanced|local-strong|cloud-balanced --confirm-disposable
       [--timeout-minutes 60] [--attempts 20]

Required secret environment variables:
  AGI_E2E_ADMIN_PASSWORD
  AGI_E2E_BOOTSTRAP_TOKEN (optional when .secrets/bootstrap_token exists)

Cloud rehearsal additionally requires the documented AGI_CLOUD_PROVIDER/model environment and
.secrets/cloud_model_api_key. This command deletes the dedicated agi-release-rehearsal volumes.
EOF
}

base_url=""
admin_email=""
model_profile=""
timeout_minutes="60"
attempts="20"
confirmed="false"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --base-url) base_url="${2:-}"; shift 2 ;;
    --admin-email) admin_email="${2:-}"; shift 2 ;;
    --model-profile) model_profile="${2:-}"; shift 2 ;;
    --timeout-minutes) timeout_minutes="${2:-}"; shift 2 ;;
    --attempts) attempts="${2:-}"; shift 2 ;;
    --confirm-disposable) confirmed="true"; shift ;;
    *) usage; exit 2 ;;
  esac
done

if [[ "$(uname -s)" != "Linux" || "$(uname -m)" != "x86_64" ]]; then
  echo "Release rehearsal must run on a separate Linux x86-64 host." >&2
  exit 2
fi
if [[ -z "${base_url}" || ! "${base_url}" =~ ^https:// || -z "${admin_email}" || -z "${model_profile}" || "${confirmed}" != "true" ]]; then
  usage
  exit 2
fi
case "${model_profile}" in local-balanced|local-strong|cloud-balanced) ;; *) usage; exit 2 ;; esac
if [[ ! "${timeout_minutes}" =~ ^[0-9]+$ ]] || (( timeout_minutes < 1 || timeout_minutes > 180 )); then
  echo "Timeout must be an integer from 1 to 180 minutes." >&2
  exit 2
fi
if [[ ! "${attempts}" =~ ^[0-9]+$ ]] || (( attempts < 20 || attempts > 100 )); then
  echo "Release qualification requires 20-100 attempts." >&2
  exit 2
fi
if [[ -z "${AGI_E2E_ADMIN_PASSWORD:-}" ]]; then
  echo "Set AGI_E2E_ADMIN_PASSWORD in the process environment." >&2
  exit 2
fi

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${root}"
if [[ -n "$(git status --porcelain)" ]]; then
  echo "Release rehearsal requires a clean Git worktree." >&2
  exit 2
fi

export COMPOSE_PROJECT_NAME="agi-release-rehearsal"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
evidence_dir="${root}/artifacts/release/rehearsal-${timestamp}"
steps_file="$(mktemp)"
manifest="${evidence_dir}/manifest.json"
backup_dir="${evidence_dir}/backup"
mkdir -p "${evidence_dir}"
started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

write_manifest() {
  local exit_code="$1"
  python3 - "${steps_file}" "${manifest}" "${started_at}" "${exit_code}" <<'PY'
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

steps_path, output_path, started_at, exit_code = sys.argv[1:]
steps = []
for line in Path(steps_path).read_text(encoding="utf-8").splitlines():
    label, status, duration = line.split("\t")
    steps.append({"name": label, "status": status, "duration_seconds": int(duration)})
payload = {
    "schema": "agi-release-rehearsal-v1",
    "started_at": started_at,
    "finished_at": datetime.now(timezone.utc).isoformat(),
    "result": "passed" if exit_code == "0" else "failed",
    "exit_code": int(exit_code),
    "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    "host": {"system": platform.system(), "machine": platform.machine()},
    "model_profile": os.environ.get("AGI_MODEL_PROFILE"),
    "steps": steps,
    "content_policy": "No prompts, source bodies, evidence excerpts, credentials, or provider keys.",
}
Path(output_path).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY
  echo "Content-safe rehearsal manifest: ${manifest}"
}

on_exit() {
  local code=$?
  trap - EXIT
  write_manifest "${code}" || true
  rm -f "${steps_file}"
  exit "${code}"
}
trap on_exit EXIT

run_step() {
  local label="$1"
  shift
  local start end code status
  start="$(date +%s)"
  set +e
  "$@"
  code=$?
  set -e
  end="$(date +%s)"
  status="passed"
  [[ ${code} -eq 0 ]] || status="failed"
  printf '%s\t%s\t%s\n' "${label}" "${status}" "$((end - start))" >> "${steps_file}"
  return "${code}"
}

base_compose=(docker compose -f docker-compose.yml -f docker-compose.production.yml)
full_compose=(docker compose -f docker-compose.yml -f docker-compose.production.yml)
if [[ "${model_profile}" == "cloud-balanced" ]]; then
  if [[ ! -s .secrets/cloud_model_api_key || -z "${AGI_CLOUD_PROVIDER:-}" ]]; then
    echo "Cloud rehearsal requires AGI_CLOUD_PROVIDER and .secrets/cloud_model_api_key." >&2
    exit 2
  fi
  full_compose+=( -f docker-compose.cloud.yml --profile cloud )
fi
full_compose+=( --profile search )

run_step "initialize-secrets" ./scripts/initialize-secrets.sh
if [[ -z "${AGI_E2E_BOOTSTRAP_TOKEN:-}" ]]; then
  export AGI_E2E_BOOTSTRAP_TOKEN="$(<.secrets/bootstrap_token)"
fi

run_step "clean-dedicated-volumes" "${base_compose[@]}" down -v --remove-orphans
export AGI_MODEL_PROFILE="local-balanced"
run_step "default-no-egress-start" "${base_compose[@]}" up -d --build --wait
run_step "default-no-egress" ./scripts/verify-no-egress.sh
run_step "default-no-egress-stop" "${base_compose[@]}" down --remove-orphans

export AGI_MODEL_PROFILE="${model_profile}"
if [[ "${model_profile}" == "local-balanced" ]]; then
  run_step "pull-local-model" ./scripts/pull-model.sh qwen3.5:9b
elif [[ "${model_profile}" == "local-strong" ]]; then
  run_step "pull-local-model" ./scripts/pull-model.sh qwen3.5:27b
fi
run_step "release-stack-start" "${full_compose[@]}" up -d --build --wait
run_step "repository-check" ./scripts/project-check.sh --live

image_id="$(docker compose images -q app)"
docker tag "${image_id}" agentic-growth-intelligence-app:release-rehearsal
run_step "release-scan" ./scripts/release-scan.sh agentic-growth-intelligence-app:release-rehearsal "${evidence_dir}/scan"
run_step "model-qualification" ./scripts/qualify-model.sh "${model_profile}" "${attempts}"
run_step "real-model-browser-journey" ./scripts/browser-real-model-e2e.sh \
  --base-url "${base_url}" \
  --admin-email "${admin_email}" \
  --model-profile "${model_profile}" \
  --timeout-minutes "${timeout_minutes}" \
  --confirm-disposable
run_step "backup" ./scripts/backup.sh "${backup_dir}"
run_step "restore" ./scripts/restore.sh "${backup_dir}"

run_step "qmd-loss" "${full_compose[@]}" stop qmd
export AGI_E2E_RESTORED_STATE="true"
export AGI_E2E_ADMIN_EMAIL="${admin_email}"
export E2E_BASE_URL="${base_url%/}"
run_step "restored-lexical-browser-state" bash -c 'cd apps/web && npx playwright test e2e/restored-release-state.spec.ts'
unset AGI_E2E_RESTORED_STATE
run_step "qmd-rebuild" "${full_compose[@]}" up -d qmd
run_step "qmd-health" bash -c 'for _ in $(seq 1 60); do status=$(curl --fail --silent http://127.0.0.1:8080/api/health | python3 -c "import json,sys; print(json.load(sys.stdin)[\"components\"][\"qmd\"])"); [[ "$status" == "ok" ]] && exit 0; sleep 2; done; exit 1'

echo "Release rehearsal passed. Keep the dedicated stack available for operator inspection."
