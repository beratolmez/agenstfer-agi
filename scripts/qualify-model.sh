#!/usr/bin/env sh
set -u

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PROFILE=${1:-local-balanced}
ATTEMPTS=${2:-20}

case "$PROFILE" in
  local-balanced|local-strong|cloud-balanced) ;;
  *) echo "Unsupported model profile: $PROFILE" >&2; exit 2 ;;
esac
case "$ATTEMPTS" in
  ''|*[!0-9]*) echo "Attempts must be an integer from 1 to 100." >&2; exit 2 ;;
esac
if [ "$ATTEMPTS" -lt 1 ] || [ "$ATTEMPTS" -gt 100 ]; then
  echo "Attempts must be an integer from 1 to 100." >&2
  exit 2
fi

# The golden-evaluation harness this script used to invoke was built on the removed
# legacy stack (chromadb + apps/services/ai-agent) and never shipped inside the image,
# so this gate has not actually run for some time. It must be rebuilt on
# agi_server.evaluation so that it is packaged with the application. Failing loudly
# here is deliberate: a release gate that silently does nothing is worse than none.
echo "model qualification harness is not available: rebuild it on agi_server.evaluation" >&2
echo "see docs/REMEDIATION_ROADMAP.md (model qualification harness)" >&2
exit 3

REPORT="evaluation-$PROFILE.json"
mkdir -p "$ROOT/artifacts/release"
docker compose -f "$ROOT/docker-compose.yml" exec -T app \
  python scripts/run-golden-eval.py \
  --profile "$PROFILE" \
  --attempts "$ATTEMPTS" \
  --output "/tmp/$REPORT"
STATUS=$?
docker compose -f "$ROOT/docker-compose.yml" cp \
  "app:/tmp/$REPORT" "$ROOT/artifacts/release/$REPORT" || exit 3
echo "Qualification report: $ROOT/artifacts/release/$REPORT"
exit "$STATUS"
