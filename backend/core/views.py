from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, JsonResponse
from django.views.decorators.http import require_GET

from ingestion.models import ImportRun
from review.models import AuditEvent

from .serializers import (
    build_dashboard_summary,
    serialize_audit_event,
    serialize_data_source,
    serialize_facility,
    serialize_import_run,
    serialize_record,
    serialize_tenant,
)
from .models import ActivityRecord, DataSourceProfile, Facility, Tenant


SAMPLE_FILE_MAP = {
    "sap": settings.PROJECT_ROOT / "sample_data" / "sap_export_demo.csv",
    "utility": settings.PROJECT_ROOT / "sample_data" / "utility_green_button_demo.xml",
    "travel": settings.PROJECT_ROOT / "sample_data" / "travel_concur_demo.json",
}


def _filtered_records(request):
    queryset = ActivityRecord.objects.select_related("tenant", "facility", "data_source")
    tenant_id = request.GET.get("tenantId")
    status = request.GET.get("status")
    source_type = request.GET.get("sourceType")

    if tenant_id:
        queryset = queryset.filter(tenant_id=tenant_id)
    if status:
        queryset = queryset.filter(review_status=status)
    if source_type:
        queryset = queryset.filter(source_type=source_type)

    return queryset.order_by("-created_at", "-id")


@require_GET
def health_view(request):
    return JsonResponse({"status": "ok", "service": "breathe-esg-prototype", "version": settings.APP_VERSION})


@require_GET
def version_view(request):
    return JsonResponse({"service": "breathe-esg-prototype", "version": settings.APP_VERSION})


@require_GET
def reference_data_view(request):
    tenants = Tenant.objects.all()
    facilities = Facility.objects.select_related("tenant").prefetch_related("aliases")
    data_sources = DataSourceProfile.objects.all()

    return JsonResponse(
        {
            "tenants": [serialize_tenant(tenant) for tenant in tenants],
            "facilities": [serialize_facility(facility) for facility in facilities],
            "dataSources": [serialize_data_source(data_source) for data_source in data_sources],
        }
    )


@require_GET
def dashboard_view(request):
    records = _filtered_records(request)
    recent_imports = ImportRun.objects.select_related("tenant", "source_document").prefetch_related("issues")[:8]
    recent_audit_events = AuditEvent.objects.select_related("tenant")[:12]

    return JsonResponse(
        {
            "summary": build_dashboard_summary(records),
            "records": [serialize_record(record) for record in records[:60]],
            "imports": [serialize_import_run(item) for item in recent_imports],
            "auditEvents": [serialize_audit_event(event) for event in recent_audit_events],
        }
    )


@require_GET
def records_view(request):
    records = _filtered_records(request)
    return JsonResponse({"records": [serialize_record(record) for record in records[:120]]})


@require_GET
def imports_view(request):
    imports = ImportRun.objects.select_related("tenant", "source_document").prefetch_related("issues")[:40]
    return JsonResponse({"imports": [serialize_import_run(item) for item in imports]})


@require_GET
def sample_file_view(request, source_type):
    sample_path = SAMPLE_FILE_MAP.get(source_type.lower())
    if not sample_path or not Path(sample_path).exists():
        raise Http404("Sample file not found.")

    return FileResponse(open(sample_path, "rb"), as_attachment=True, filename=sample_path.name)
