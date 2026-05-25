# Breathe ESG Prototype

Version `0.1.0`

This is a  prototype for the Breathe ESG assignment. It ingests three realistic enterprise source shapes, normalizes them into one review ledger, flags suspicious rows, and lets an analyst approve or reject records with audit history.

## Why this shape

- `Django + JSON API`: . Django handles the relational model, migrations, admin, and seeding cleanly.
- `React + Vite`: React satisfies the frontend requirement while Vite keeps the client small and fast to build. The bundle is emitted into Django static files so the app runs as one deployable service.
- `SQLite for local launch`: 
- `One normalized ledger`: analysts review one `ActivityRecord` shape instead of learning three source-specific UIs. Source-specific raw payloads are still preserved for traceability.
- `Idempotent seeding and imports`: the seed script can be rerun safely, and records dedupe on `(tenant, source_type, external_id)` so repeated sample syncs do not explode the dataset.

## What it does

- Ingests SAP fuel and procurement rows from a flat export CSV.
- Ingests utility electricity rows from a Green Button-style XML feed.
- Syncs Concur-like air, hotel, and ground travel receipts from a local demo API snapshot.
- Normalizes everything into one multi-tenant review queue.
- Flags anomalies such as unmapped facilities, currency conversions, non-calendar utility billing periods, and derived flight distance.
- Tracks import runs, row issues, uploaded source documents, and analyst review events.

## File hierarchy

```text
breathe-esg-prototype/
├── backend/
│   ├── config/
│   │   ├── logging.py            # JSON log formatter
│   │   ├── settings.py           # Django settings, static/media wiring, version
│   │   ├── urls.py               # API routing + SPA entry point
│   │   └── views.py              # Index template view
│   ├── core/
│   │   ├── constants.py          # Shared enums for source, scope, review, import state
│   │   ├── management/commands/
│   │   │   └── seed_demo_data.py # Idempotent tenant/facility/factor seeding + sample loading
│   │   ├── models.py             # Tenant, Facility, FacilityAlias, DataSourceProfile, EmissionFactor, ActivityRecord
│   │   ├── serializers.py        # JSON shaping for dashboard responses
│   │   ├── tests.py              # Health + dashboard integration tests
│   │   ├── urls.py               # Read-side API endpoints
│   │   └── views.py              # Health, version, dashboard, sample download endpoints
│   ├── ingestion/
│   │   ├── models.py             # SourceDocument, ImportRun, ImportIssue
│   │   ├── parsers.py            # SAP CSV, utility XML, travel JSON normalization logic
│   │   ├── services.py           # Import orchestration, dedupe, facility mapping, audit writes
│   │   ├── tests.py              # Import API integration tests
│   │   ├── urls.py               # Write-side import endpoints
│   │   └── views.py              # SAP upload, utility upload, travel sync endpoints
│   ├── review/
│   │   ├── models.py             # AuditEvent
│   │   ├── tests.py              # Review workflow integration test
│   │   ├── urls.py               # Review endpoint
│   │   └── views.py              # Approve/reject API
│   └── templates/
│       └── index.html            # Django shell for the built React bundle
├── deploy/
│   └── systemd/
│       └── breathe-esg-prototype.service
├── render.yaml                   # Render blueprint with build, start, and health check config
├── frontend/
│   ├── src/
│   │   ├── App.jsx               # Analyst dashboard UI
│   │   ├── App.css               # Dashboard layout + visual system
│   │   ├── index.css             # Global typography, palette, page frame
│   │   └── main.jsx              # React entry point
│   ├── package.json              # Frontend package manifest
│   ├── package-lock.json         # Locked frontend dependency graph
│   └── vite.config.js            # Emits static assets into Django
├── sample_data/
│   ├── sap_export_demo.csv
│   ├── utility_green_button_demo.xml
│   └── travel_concur_demo.json
├── scripts/
│   ├── build_frontend.sh         # Local frontend build helper
│   ├── install.sh                # Local venv + npm install
│   ├── install_windows.ps1       # Windows venv + npm install helper
│   ├── launch_local.sh           # Local migrate/seed/build + gunicorn launch
│   ├── launch_windows.ps1        # Windows migrate/seed/build + Django runserver launch
│   ├── render_build.sh           # Render build hook for dependency install + collectstatic
│   ├── render_release.sh         # Render pre-deploy hook for migrations + idempotent seed data
│   ├── render_start.sh           # Render start hook using Render's PORT env var
│   ├── run_frontend_windows.ps1  # Optional Windows Vite dev server helper
│   ├── run_tests.sh              # Backend tests + frontend build verification
│   └── run_tests_windows.ps1     # Windows backend tests + frontend build verification
├── build.sh                      # Root Render build wrapper for manual service setup
├── start.sh                      # Root Render start wrapper for manual service setup
├── .python-version               # Pins Render to the tested Python version
├── CHANGES.md
├── DECISIONS.md
├── MODEL.md
├── README.md
├── SOURCES.md
├── TRADEOFFS.md
└── requirements.txt
```

## Data model and why

### `Tenant`

- Why it exists: the assignment explicitly asks for multi-tenancy.
- Why it is small: the prototype only needs the tenant boundary, sector, and reporting currency. Anything else would be speculative.

### `Facility`

- Why it exists: emissions data lands against plants, offices, usage points, or cost centers. Analysts need a stable facility anchor for rollups.
- Why it is separate from source records: one facility can appear across SAP, utility, and travel feeds.

### `FacilityAlias`

- Why it exists: this is the main normalization optimization.
- Why it is better than extra columns on `Facility`: each source names the same place differently. A separate alias table prevents sparse columns like `sap_plant_code`, `utility_usage_point`, `travel_cost_center`, and it scales when new connectors are added.

### `DataSourceProfile`

- Why it exists: every tenant can have multiple connectors with different modes, labels, and config.
- Why it is separate from `Tenant`: ingestion settings change independently from tenant identity.

### `SourceDocument`

- Why it exists: the review queue must preserve the original upload or API snapshot for source-of-truth tracking.
- Why it stores checksum + preview: checksum helps dedupe/debug repeat loads, while preview gives operators context without opening the file.

### `ImportRun`

- Why it exists: analysts and operators need batch-level observability, not just row-level data.
- Why it stores counters: import status, accepted count, flagged count, rejected count, and issue count answer “what happened?” immediately.

### `ImportIssue`

- Why it exists: failed rows and warnings should not pollute the normalized ledger.
- Why it is separate from `ActivityRecord`: a row can fail before a normalized record exists.

### `EmissionFactor`

- Why it exists: factor logic should not be hard-coded inside parsers.
- Why it is separate from `ActivityRecord`: the prototype uses seed data today, but a production system would replace or version factor sets independently.

### `ActivityRecord`

- Why it exists: this is the normalized review ledger.
- Why it is the central table: analysts care about one reviewable record shape regardless of source.
- Why it stores both `source_payload` and `normalized_payload`: review requires proof of how the normalized row was derived.
- Why it has `review_status`, `review_note`, `reviewed_by`, and `locked_at`: the assignment explicitly requires analyst sign-off before audit.
- Why it has the unique key `(tenant, source_type, external_id)`: repeated syncs update the same business row instead of creating duplicates. That keeps seeding and connector retries idempotent.

### `AuditEvent`

- Why it exists: import start/completion and approve/reject actions need an immutable trail.
- Why it is append-only: audit history loses value if edits overwrite previous decisions.

## Source choices and why

### SAP

- Chosen shape: flat CSV export from SAP MM / procurement reporting.
- Why: in a 4-day prototype, manual enterprise onboarding usually starts with extracts finance or operations teams can actually hand over. The parser still uses realistic SAP-style columns like purchase document, plant, material group, quantity, unit, amount, and currency.
- Normalization rule: fuel-like material groups go to Scope 1 with liter normalization; procurement rows go to Scope 3 with spend-based normalization.

### Utility electricity

- Chosen shape: Green Button-style XML subset with `UsagePoint`, `MeterReading`, `ReadingType`, `IntervalReading`, tariff metadata, and a billing period.
- Why: it captures the real headaches the assignment called out, especially units, billing periods, and tariff context.
- Normalization rule: interval readings roll up into kWh over the billing period and stay tied to the source usage point.

### Corporate travel

- Chosen shape: Concur-like travel receipt feed covering air, hotel, and ground.
- Why: the receipt schemas map cleanly to the three categories the assignment asked for and give enough detail to demonstrate different factor logic.
- Normalization rule: air uses miles, hotel uses room-nights, ground uses miles. Missing air distance is derived from airport pairs when the lookup is known, otherwise the row is rejected.

## Running it

Linux/macOS:

```bash
cd /opt/apps/breathe-esg-prototype
./scripts/install.sh
./scripts/launch_local.sh
```

Windows PowerShell:

```powershell
cd BreatheESG_Assignment
git checkout feature/breathe-esg-prototype
.\scripts\install_windows.ps1
.\scripts\launch_windows.ps1
```

The app listens on `http://127.0.0.1:8810` by default. The JSON API is under `/api/v1/...`.

For React dev-server mode on Windows, keep `launch_windows.ps1` running in one terminal and run this in a second terminal:

```powershell
.\scripts\run_frontend_windows.ps1
```

Open `http://127.0.0.1:5173`. Vite proxies `/api/...` to the Django backend on `http://127.0.0.1:8810`.

## Deploy on Render

- Use the repository root as the Render service root.
- Runtime: Python
- Build command: `bash ./build.sh`
- Pre-deploy command: `bash ./scripts/render_release.sh`
- Start command: `bash ./start.sh`
- Health check path: `/api/v1/health`
- The Render start script binds Gunicorn to `0.0.0.0:$PORT`; migrations and idempotent demo seeding run in the pre-deploy step.
- Frontend assets are committed under `backend/static/frontend`, so Render does not need `npm` for this deploy path.
- This prototype still uses SQLite and local media storage. That is fine for a demo deploy, but both the database file and uploaded files are ephemeral on Render unless you move to managed persistence.

## Test it

```bash
cd /opt/apps/breathe-esg-prototype
./scripts/run_tests.sh
```

Windows PowerShell:

```powershell
.\scripts\run_tests_windows.ps1
```

## Main API routes

- `GET /api/v1/health`
- `GET /api/v1/version`
- `GET /api/v1/reference-data`
- `GET /api/v1/dashboard`
- `GET /api/v1/records`
- `GET /api/v1/imports`
- `GET /api/v1/sample-files/<sap|utility|travel>`
- `POST /api/v1/imports/sap`
- `POST /api/v1/imports/utility`
- `POST /api/v1/imports/travel-sync`
- `POST /api/v1/records/<id>/review`

## Why the README points to other docs

The README carries the file hierarchy, the model inventory, and the main reasons behind the architecture because that was explicitly requested. The deeper assignment artifacts live in:

- [MODEL.md](MODEL.md)
- [DECISIONS.md](DECISIONS.md)
- [TRADEOFFS.md](TRADEOFFS.md)
- [SOURCES.md](SOURCES.md)
