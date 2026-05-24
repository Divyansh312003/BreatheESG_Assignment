import json
from datetime import datetime, timezone

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.constants import AuditEventType, ReviewStatus
from core.serializers import serialize_record
from core.models import ActivityRecord

from .models import AuditEvent


@csrf_exempt
@require_POST
def review_record_view(request, record_id):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    record = ActivityRecord.objects.select_related("tenant").filter(id=record_id).first()
    if record is None:
        return JsonResponse({"error": "Record not found."}, status=404)

    review_status = payload.get("reviewStatus")
    actor = payload.get("actor") or "Demo Analyst"
    note = payload.get("note", "").strip()
    if review_status not in {ReviewStatus.APPROVED, ReviewStatus.REJECTED}:
        return JsonResponse({"error": "reviewStatus must be APPROVED or REJECTED."}, status=400)

    record.review_status = review_status
    record.review_note = note
    record.reviewed_by = actor
    record.reviewed_at = datetime.now(timezone.utc)
    record.locked_at = datetime.now(timezone.utc) if review_status == ReviewStatus.APPROVED else None
    record.save(
        update_fields=[
            "review_status",
            "review_note",
            "reviewed_by",
            "reviewed_at",
            "locked_at",
            "updated_at",
        ]
    )

    AuditEvent.objects.create(
        tenant=record.tenant,
        import_run=record.import_run,
        activity_record=record,
        actor=actor,
        event_type=(
            AuditEventType.RECORD_APPROVED
            if review_status == ReviewStatus.APPROVED
            else AuditEventType.RECORD_REJECTED
        ),
        message="{} record {}.".format(review_status.title(), record.external_id),
        payload={"note": note},
    )

    return JsonResponse({"record": serialize_record(record)})
