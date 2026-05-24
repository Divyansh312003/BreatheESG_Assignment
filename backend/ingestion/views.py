import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.serializers import serialize_import_run
from core.models import Tenant
from core.constants import IngestionMode, SourceType

from .services import process_import, sync_travel_demo


def _tenant_from_request(request, payload):
    tenant_id = payload.get("tenantId") or request.POST.get("tenantId")
    if not tenant_id:
        return None
    return Tenant.objects.filter(id=tenant_id).first()


def _actor_from_request(request, payload):
    return (
        payload.get("actor")
        or request.POST.get("actor")
        or request.headers.get("X-Actor")
        or "Demo Analyst"
    )


@csrf_exempt
@require_POST
def sap_import_view(request):
    tenant = _tenant_from_request(request, {})
    upload = request.FILES.get("file")
    actor = _actor_from_request(request, {})
    if tenant is None or upload is None:
        return JsonResponse({"error": "tenantId and file are required."}, status=400)

    import_run = process_import(
        tenant=tenant,
        source_type=SourceType.SAP,
        ingestion_mode=IngestionMode.FILE_UPLOAD,
        actor=actor,
        file_name=upload.name,
        file_bytes=upload.read(),
    )
    return JsonResponse({"importRun": serialize_import_run(import_run)})


@csrf_exempt
@require_POST
def utility_import_view(request):
    tenant = _tenant_from_request(request, {})
    upload = request.FILES.get("file")
    actor = _actor_from_request(request, {})
    if tenant is None or upload is None:
        return JsonResponse({"error": "tenantId and file are required."}, status=400)

    import_run = process_import(
        tenant=tenant,
        source_type=SourceType.UTILITY,
        ingestion_mode=IngestionMode.FILE_UPLOAD,
        actor=actor,
        file_name=upload.name,
        file_bytes=upload.read(),
    )
    return JsonResponse({"importRun": serialize_import_run(import_run)})


@csrf_exempt
@require_POST
def travel_sync_view(request):
    payload = json.loads(request.body.decode("utf-8") or "{}")
    tenant = _tenant_from_request(request, payload)
    actor = _actor_from_request(request, payload)
    if tenant is None:
        return JsonResponse({"error": "tenantId is required."}, status=400)

    import_run = sync_travel_demo(tenant=tenant, actor=actor)
    return JsonResponse({"importRun": serialize_import_run(import_run)})
