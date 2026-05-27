#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${PROJECT_ROOT}"

export PYTHONPATH="${PROJECT_ROOT}/backend"
export DJANGO_SETTINGS_MODULE="config.settings"
export DJANGO_SECRET_KEY="${DJANGO_SECRET_KEY:-build-phase-placeholder-secret-key-not-used-in-prod}"
export DEBUG="false"

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

mkdir -p backend/staticfiles

python backend/manage.py collectstatic --noinput --clear
