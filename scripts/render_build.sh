#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${PROJECT_ROOT}"

export PYTHONPATH="${PROJECT_ROOT}/backend"
export DJANGO_SETTINGS_MODULE="config.settings"

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python backend/manage.py collectstatic --noinput
