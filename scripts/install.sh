#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"

if [ ! -x "${VENV_DIR}/bin/python" ]; then
  python3.11 -m venv "${VENV_DIR}"
fi

"${VENV_DIR}/bin/pip" install -r "${PROJECT_ROOT}/requirements.txt"

if [ ! -d "${PROJECT_ROOT}/frontend/node_modules" ]; then
  (cd "${PROJECT_ROOT}/frontend" && npm install)
fi
