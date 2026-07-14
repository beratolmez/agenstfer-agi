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
