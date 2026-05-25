#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="${APP_HOST:-0.0.0.0}"
PORT="${PORT:-${APP_PORT:-10000}}"
WORKERS="${GUNICORN_WORKERS:-2}"

cd "${PROJECT_ROOT}"

exec gunicorn \
  --chdir "${PROJECT_ROOT}/backend" \
  --bind "${HOST}:${PORT}" \
  --workers "${WORKERS}" \
  --access-logfile - \
  --error-logfile - \
  config.wsgi:application
