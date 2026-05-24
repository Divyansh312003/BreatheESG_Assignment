import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction

from core.constants import AuditEventType, ImportStatus, IngestionMode, IssueSeverity, ReviewStatus, SourceType
from core.models import ActivityRecord, DataSourceProfile, EmissionFactor, Facility, FacilityAlias, Tenant
from review.models import AuditEvent

from .models import ImportIssue, ImportRun, SourceDocument
from .parsers import parse_sap_export, parse_travel_receipts, parse_utility_green_button


PARSER_MAP = {
    SourceType.SAP: parse_sap_export,
    SourceType.UTILITY: parse_utility_green_button,
    SourceType.TRAVEL: parse_travel_receipts,
}


def resolve_facility(tenant, source_type, alias):
    if not alias:
        return None

    direct_match = Facility.objects.filter(tenant=tenant, code=alias).first()
    if direct_match:
        return direct_match

    alias_match = FacilityAlias.objects.select_related("facility").filter(
        facility__tenant=tenant,
        source_type=source_type,
        alias=alias,
    ).first()
    return alias_match.facility if alias_match else None


def _source_profile_for_tenant(tenant, source_type):
    return DataSourceProfile.objects.filter(tenant=tenant, source_type=source_type).first()


def _estimate_emissions(factor_lookup, factor_code, normalized_quantity):
    factor = factor_lookup.get(factor_code)
    if factor is None or normalized_quantity is None:
        return None
    return factor.kg_co2e_per_unit * normalized_quantity


def _create_audit_event(tenant, import_run, activity_record, event_type, actor, message, payload=None):
    AuditEvent.objects.create(
        tenant=tenant,
        import_run=import_run,
        activity_record=activity_record,
        actor=actor,
        event_type=event_type,
        message=message,
        payload=payload or {},
    )


def process_import(tenant, source_type, ingestion_mode, actor, file_name, file_bytes):
    parser = PARSER_MAP[source_type]
    source_profile = _source_profile_for_tenant(tenant, source_type)
    checksum = hashlib.sha256(file_bytes).hexdigest()

    with transaction.atomic():
        source_document = SourceDocument.objects.create(
            tenant=tenant,
            data_source=source_profile,
            source_type=source_type,
            ingestion_mode=ingestion_mode,
            original_filename=file_name,
            checksum=checksum,
        )
        source_document.document.save(file_name, ContentFile(file_bytes), save=True)

        import_run = ImportRun.objects.create(
            tenant=tenant,
            data_source=source_profile,
            source_document=source_document,
            source_type=source_type,
            ingestion_mode=ingestion_mode,
            status=ImportStatus.PROCESSING,
            requested_by=actor or "Demo Analyst",
        )

        _create_audit_event(
            tenant,
            import_run,
            None,
            AuditEventType.IMPORT_STARTED,
            actor,
            "Started {} import.".format(source_type),
            {"fileName": file_name},
        )

        parsed = parser(file_bytes)
        factor_lookup = EmissionFactor.objects.in_bulk(field_name="code")
        scope_counts = defaultdict(int)
        category_counts = defaultdict(int)
        accepted_count = 0
        flagged_count = 0

        source_document.payload_preview = {"items": parsed["preview"]}
        source_document.save(update_fields=["payload_preview"])

        for issue in parsed["issues"]:
            ImportIssue.objects.create(import_run=import_run, **issue)

        for payload in parsed["records"]:
            suspicion_reasons = list(payload.get("suspicion_reasons", []))
            facility_alias = payload.pop("facility_alias", "")
            factor_code = payload.pop("factor_code")
            facility = resolve_facility(tenant, source_type, facility_alias)
            if facility is None and facility_alias:
                suspicion_reasons.append("Facility alias {} is not mapped.".format(facility_alias))

            estimated_kg_co2e = _estimate_emissions(
                factor_lookup,
                factor_code,
                payload.get("normalized_quantity"),
            )
            if estimated_kg_co2e is None:
                suspicion_reasons.append("No emission factor was found for {}.".format(factor_code))

            defaults = dict(payload)
            defaults.update(
                {
                    "tenant": tenant,
                    "facility": facility,
                    "data_source": source_profile,
                    "import_run": import_run,
                    "source_document": source_document,
                    "source_type": source_type,
                    "review_status": ReviewStatus.PENDING,
                    "estimated_kg_co2e": estimated_kg_co2e,
                    "suspicion_reasons": suspicion_reasons,
                    "suspicion_score": len(suspicion_reasons),
                    "review_note": "",
                    "reviewed_by": "",
                    "reviewed_at": None,
                    "locked_at": None,
                    "edited_fields": [],
                }
            )

            activity_record, _created = ActivityRecord.objects.update_or_create(
                tenant=tenant,
                source_type=source_type,
                external_id=payload["external_id"],
                defaults=defaults,
            )

            accepted_count += 1
            scope_counts[activity_record.scope] += 1
            category_counts[activity_record.category] += 1

            if suspicion_reasons:
                flagged_count += 1
                ImportIssue.objects.create(
                    import_run=import_run,
                    severity=IssueSeverity.WARNING,
                    line_number=payload.get("source_line_number"),
                    field_name="review",
                    message="; ".join(suspicion_reasons),
                    raw_payload={"externalId": activity_record.external_id},
                )

        rejected_count = parsed["rejected_count"]
        issue_count = import_run.issues.count()
        import_run.accepted_count = accepted_count
        import_run.flagged_count = flagged_count
        import_run.rejected_count = rejected_count
        import_run.issue_count = issue_count
        import_run.summary = {
            "scopeCounts": dict(scope_counts),
            "categoryCounts": dict(category_counts),
            "previewCount": len(parsed["preview"]),
        }
        import_run.status = (
            ImportStatus.COMPLETED_WITH_ISSUES if issue_count else ImportStatus.COMPLETED
        )
        import_run.save()

        _create_audit_event(
            tenant,
            import_run,
            None,
            AuditEventType.IMPORT_COMPLETED,
            actor,
            "Completed {} import.".format(source_type),
            {
                "acceptedCount": accepted_count,
                "flaggedCount": flagged_count,
                "rejectedCount": rejected_count,
            },
        )

    return import_run


def sync_travel_demo(tenant, actor):
    sample_path = settings.PROJECT_ROOT / "sample_data" / "travel_concur_demo.json"
    file_bytes = Path(sample_path).read_bytes()
    return process_import(
        tenant=tenant,
        source_type=SourceType.TRAVEL,
        ingestion_mode=IngestionMode.API_PULL,
        actor=actor,
        file_name="travel_concur_demo.json",
        file_bytes=file_bytes,
    )
