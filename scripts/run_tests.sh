#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PROJECT_ROOT}/.venv/bin/python"

(cd "${PROJECT_ROOT}/backend" && "${PYTHON}" manage.py test)
(cd "${PROJECT_ROOT}/frontend" && npm run build)
