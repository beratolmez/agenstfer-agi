#!/usr/bin/env bash
set -euo pipefail

directory="${1:-.secrets}"
mkdir -p "${directory}"
chmod 700 "${directory}"
for name in bootstrap_token session_secret master_key; do
  path="${directory}/${name}"
  if [[ -e "${path}" ]]; then
    echo "Preserved existing secret: ${path}"
    continue
  fi
  umask 077
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -base64 48 > "${path}"
  else
    head -c 48 /dev/urandom | base64 > "${path}"
  fi
  chmod 600 "${path}"
  echo "Created secret: ${path}"
done
echo "Store the bootstrap token securely; it is required only for the first admin."
