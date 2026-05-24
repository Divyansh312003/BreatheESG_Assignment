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
