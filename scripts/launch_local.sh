#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PROJECT_ROOT}/.venv/bin/python"
GUNICORN="${PROJECT_ROOT}/.venv/bin/gunicorn"
HOST="${APP_HOST:-0.0.0.0}"
PORT="${APP_PORT:-8810}"

(cd "${PROJECT_ROOT}/backend" && "${PYTHON}" manage.py migrate --noinput)
(cd "${PROJECT_ROOT}/backend" && "${PYTHON}" manage.py seed_demo_data --load-samples)
(cd "${PROJECT_ROOT}/frontend" && npm run build >/dev/null)

exec "${GUNICORN}" \
  --chdir "${PROJECT_ROOT}/backend" \
  --bind "${HOST}:${PORT}" \
  --workers 2 \
  --access-logfile - \
  --error-logfile - \
  config.wsgi:application
