from django.contrib import admin

from .models import ImportIssue, ImportRun, SourceDocument


@admin.register(SourceDocument)
class SourceDocumentAdmin(admin.ModelAdmin):
    list_display = ("tenant", "source_type", "ingestion_mode", "original_filename", "created_at")
    list_filter = ("tenant", "source_type", "ingestion_mode")
    search_fields = ("original_filename", "checksum")


@admin.register(ImportRun)
class ImportRunAdmin(admin.ModelAdmin):
    list_display = (
        "tenant",
        "source_type",
        "status",
        "accepted_count",
        "flagged_count",
        "rejected_count",
        "issue_count",
        "created_at",
    )
    list_filter = ("tenant", "source_type", "status", "ingestion_mode")
    search_fields = ("tenant__name", "requested_by")


@admin.register(ImportIssue)
class ImportIssueAdmin(admin.ModelAdmin):
    list_display = ("import_run", "severity", "line_number", "field_name", "message")
    list_filter = ("severity",)
    search_fields = ("message", "field_name")

# Register your models here.
