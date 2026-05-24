# MODEL

## Relationship summary

- `Tenant 1 -> many Facility`
- `Facility 1 -> many FacilityAlias`
- `Tenant 1 -> many DataSourceProfile`
- `Tenant 1 -> many SourceDocument`
- `Tenant 1 -> many ImportRun`
- `ImportRun 1 -> many ImportIssue`
- `ImportRun 1 -> many ActivityRecord`
- `SourceDocument 1 -> many ActivityRecord`
- `Tenant 1 -> many ActivityRecord`
- `Facility 1 -> many ActivityRecord`
- `Tenant 1 -> many AuditEvent`
- `ActivityRecord 1 -> many AuditEvent`

## Why this model works for the assignment

### Multi-tenancy

`Tenant` is the ownership root for facilities, connectors, import runs, documents, and ledger rows. That keeps the prototype honest about tenant isolation from day one.

### Source-of-truth tracking

`SourceDocument` stores the original upload or synced API snapshot. `ActivityRecord.source_payload` preserves the source row or receipt fragment. `ActivityRecord.normalized_payload` preserves the normalized intermediate form. Together these answer:

- which source created the row
- what the raw payload looked like
- how the normalized fields were derived

### Review and locking

`ActivityRecord.review_status`, `review_note`, `reviewed_by`, `reviewed_at`, and `locked_at` model the analyst workflow directly. `AuditEvent` records the actual action history behind those state changes.

### Row-level failures without ledger pollution

`ImportIssue` captures batch and row problems that do not deserve a normalized ledger row. That separation matters because analysts should review business activity, not parser exceptions.

### Optimization choices

#### `FacilityAlias`

This is the key normalization optimization. Instead of repeating source-specific identifiers on every `ActivityRecord`, aliases are resolved once against `Facility`. The result:

- less duplication
- cheaper joins in the review UI
- easier connector growth when new sources arrive

#### `(tenant, source_type, external_id)` uniqueness

This makes seed/sample imports idempotent and keeps connector retries from duplicating rows. It is the smallest useful natural key for the prototype.

#### `EmissionFactor` as reference data

Factors are seeded data, not parser logic. That keeps parsing focused on structure and normalization while allowing factor replacement later without rewriting ingestion code.
