# Changes

## 2026-05-24

- Created a separate project directory at `/opt/apps/breathe-esg-prototype`.
- Initialized a dedicated git repository on `feature/breathe-esg-prototype`.
- Built a Django + React prototype for SAP, utility, and travel ingestion with a unified review queue.
- Added multi-tenant reference data, source document tracking, import runs, import issues, normalized activity records, emission factors, and audit events.
- Added realistic bundled sample data plus an idempotent `seed_demo_data` command.
- Added integration tests for dashboard loading, import APIs, and record approval.
- Added install, build, test, and launch scripts plus a systemd unit template.
- Downgraded the backend from Django 5 to Django 4.2 LTS because the host SQLite version is `3.26.0`, which cannot run Django 5.

## 2026-05-25

- Added a Render deployment blueprint at `render.yaml` with explicit build, start, and health check settings.
- Added `scripts/render_build.sh` and `scripts/render_start.sh` so Render installs Python dependencies, collects static assets, listens on `PORT`, runs migrations, and reseeds demo data at boot.
- Pinned the Render Python runtime with `.python-version` to `3.11.13`, matching the tested local environment.
- Updated Django settings so Render can populate `ALLOWED_HOSTS` from `RENDER_EXTERNAL_HOSTNAME`, trust the HTTPS proxy headers, and default `DEBUG` off in hosted environments.
- Stopped ignoring committed frontend build artifacts, which avoids an `npm` dependency in the Render Python runtime.
- Documented the Render deployment path and the SQLite/media persistence tradeoff in `README.md`.

## 2026-05-25 Render deployment hardening

- Added root-level `build.sh` and `start.sh` wrappers so manually configured Render services can use simple commands from the repository root.
- Added `scripts/render_release.sh` and moved migrations plus idempotent demo seeding into Render's pre-deploy phase.
- Updated `render.yaml` to use the root wrappers and `preDeployCommand`, keeping the web start command focused on binding Gunicorn to Render's assigned port.

## 2026-05-25 npm registry fix

- Added `frontend/.npmrc` to force frontend installs to use the public npm registry for this project.
- Rewrote frontend lockfile package URLs away from the internal registry so `npm install` works on public networks.
