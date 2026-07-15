#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 --base-url URL --admin-email EMAIL --confirm-disposable [--model-profile PROFILE] [--timeout-minutes N]" >&2
  echo "Set AGI_E2E_ADMIN_PASSWORD and, for a clean install, AGI_E2E_BOOTSTRAP_TOKEN in the process environment." >&2
}

base_url=""
admin_email=""
model_profile="local-balanced"
timeout_minutes="60"
confirmed="false"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --base-url) base_url="${2:-}"; shift 2 ;;
    --admin-email) admin_email="${2:-}"; shift 2 ;;
    --model-profile) model_profile="${2:-}"; shift 2 ;;
    --timeout-minutes) timeout_minutes="${2:-}"; shift 2 ;;
    --confirm-disposable) confirmed="true"; shift ;;
    *) usage; exit 2 ;;
  esac
done
if [[ -z "${base_url}" || -z "${admin_email}" || -z "${AGI_E2E_ADMIN_PASSWORD:-}" || "${confirmed}" != "true" ]]; then
  usage
  exit 2
fi
case "${model_profile}" in local-balanced|local-strong|cloud-balanced) ;; *) echo "Unsupported model profile." >&2; exit 2 ;; esac
if [[ ! "${timeout_minutes}" =~ ^[0-9]+$ ]] || (( timeout_minutes < 1 || timeout_minutes > 180 )); then
  echo "Timeout must be an integer from 1 to 180 minutes." >&2
  exit 2
fi
if [[ ! "${base_url}" =~ ^https:// && ! "${base_url}" =~ ^http://(localhost|127\.0\.0\.1|\[::1\])([:/]|$) ]]; then
  echo "Use HTTPS for non-loopback release targets." >&2
  exit 2
fi

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export AGI_E2E_REAL_MODEL="true"
export AGI_E2E_CONFIRM_DISPOSABLE="true"
export AGI_E2E_ADMIN_EMAIL="${admin_email}"
export AGI_E2E_MODEL_PROFILE="${model_profile}"
export AGI_E2E_TIMEOUT_MS="$((timeout_minutes * 60 * 1000))"
export E2E_BASE_URL="${base_url%/}"
cd "${root}/apps/web"
npx playwright test e2e/real-model-happy-path.spec.ts
