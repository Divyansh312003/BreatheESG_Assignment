from decimal import Decimal

from .models import ActivityRecord, DataSourceProfile, Facility, Tenant


def decimal_to_float(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return value


def serialize_tenant(tenant):
    return {
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
        "sector": tenant.sector,
        "reportingCurrency": tenant.reporting_currency,
    }


def serialize_facility(facility):
    aliases = [
        {"sourceType": alias.source_type, "alias": alias.alias}
        for alias in facility.aliases.all()
    ]
    return {
        "id": facility.id,
        "tenantId": facility.tenant_id,
        "code": facility.code,
        "name": facility.name,
        "countryCode": facility.country_code,
        "city": facility.city,
        "timezone": facility.timezone,
        "aliases": aliases,
    }


def serialize_data_source(data_source):
    return {
        "id": data_source.id,
        "tenantId": data_source.tenant_id,
        "sourceType": data_source.source_type,
        "label": data_source.label,
        "ingestionMode": data_source.ingestion_mode,
        "isActive": data_source.is_active,
        "config": data_source.config,
    }


def serialize_record(record):
    return {
        "id": record.id,
        "tenantId": record.tenant_id,
        "tenantName": record.tenant.name,
        "facilityId": record.facility_id,
        "facilityName": record.facility.name if record.facility else "Unmapped Facility",
        "sourceType": record.source_type,
        "dataSourceLabel": record.data_source.label if record.data_source else "",
        "category": record.category,
        "scope": record.scope,
        "reviewStatus": record.review_status,
        "externalId": record.external_id,
        "sourceDocumentIdentifier": record.source_document_identifier,
        "activityDate": record.activity_date.isoformat(),
        "periodStart": record.period_start.isoformat() if record.period_start else None,
        "periodEnd": record.period_end.isoformat() if record.period_end else None,
        "description": record.description,
        "quantityValue": decimal_to_float(record.quantity_value),
        "quantityUnit": record.quantity_unit,
        "normalizedQuantity": decimal_to_float(record.normalized_quantity),
        "normalizedUnit": record.normalized_unit,
        "currencyCode": record.currency_code,
        "spendAmount": decimal_to_float(record.spend_amount),
        "estimatedKgCo2e": decimal_to_float(record.estimated_kg_co2e),
        "suspicionScore": record.suspicion_score,
        "suspicionReasons": record.suspicion_reasons,
        "reviewNote": record.review_note,
        "reviewedBy": record.reviewed_by,
        "reviewedAt": record.reviewed_at.isoformat() if record.reviewed_at else None,
        "sourcePayload": record.source_payload,
        "normalizedPayload": record.normalized_payload,
        "editedFields": record.edited_fields,
        "createdAt": record.created_at.isoformat(),
    }


def serialize_import_issue(issue):
    return {
        "id": issue.id,
        "severity": issue.severity,
        "lineNumber": issue.line_number,
        "fieldName": issue.field_name,
        "message": issue.message,
        "rawPayload": issue.raw_payload,
    }


def serialize_import_run(import_run):
    return {
        "id": import_run.id,
        "tenantId": import_run.tenant_id,
        "tenantName": import_run.tenant.name,
        "sourceType": import_run.source_type,
        "ingestionMode": import_run.ingestion_mode,
        "status": import_run.status,
        "requestedBy": import_run.requested_by,
        "acceptedCount": import_run.accepted_count,
        "flaggedCount": import_run.flagged_count,
        "rejectedCount": import_run.rejected_count,
        "issueCount": import_run.issue_count,
        "summary": import_run.summary,
        "sourceDocument": import_run.source_document.original_filename if import_run.source_document else "",
        "createdAt": import_run.created_at.isoformat(),
        "issues": [serialize_import_issue(issue) for issue in import_run.issues.all()[:6]],
    }


def serialize_audit_event(event):
    return {
        "id": event.id,
        "tenantId": event.tenant_id,
        "eventType": event.event_type,
        "actor": event.actor,
        "message": event.message,
        "payload": event.payload,
        "createdAt": event.created_at.isoformat(),
    }


def build_dashboard_summary(records):
    total_estimated = sum((record.estimated_kg_co2e or Decimal("0")) for record in records)
    return {
        "totalRecords": records.count(),
        "pendingReview": records.filter(review_status="PENDING").count(),
        "approved": records.filter(review_status="APPROVED").count(),
        "rejected": records.filter(review_status="REJECTED").count(),
        "flagged": records.exclude(suspicion_score=0).count(),
        "totalEstimatedKgCo2e": float(total_estimated),
        "byScope": {
            "scope1": records.filter(scope="SCOPE_1").count(),
            "scope2": records.filter(scope="SCOPE_2").count(),
            "scope3": records.filter(scope="SCOPE_3").count(),
        },
        "bySourceType": {
            "sap": records.filter(source_type="SAP").count(),
            "utility": records.filter(source_type="UTILITY").count(),
            "travel": records.filter(source_type="TRAVEL").count(),
        },
    }
