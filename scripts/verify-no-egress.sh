#!/usr/bin/env bash
set -euo pipefail

app_id="$(docker compose ps -q app)"
if [[ -z "${app_id}" ]]; then
  echo "The app service must be running." >&2
  exit 1
fi
if docker exec "${app_id}" python -c "import urllib.request; urllib.request.urlopen('https://example.com', timeout=3)" >/dev/null 2>&1; then
  echo "Unexpected external network access from the app container." >&2
  exit 1
fi
echo "Default app network correctly blocks external egress."
