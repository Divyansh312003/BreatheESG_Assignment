from django.db import models

from core.constants import ImportStatus, IngestionMode, IssueSeverity, SourceType


class SourceDocument(models.Model):
    tenant = models.ForeignKey("core.Tenant", on_delete=models.CASCADE, related_name="source_documents")
    data_source = models.ForeignKey(
        "core.DataSourceProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_documents",
    )
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    ingestion_mode = models.CharField(max_length=20, choices=IngestionMode.choices)
    original_filename = models.CharField(max_length=255)
    checksum = models.CharField(max_length=64)
    document = models.FileField(upload_to="source_documents/%Y/%m/%d/", blank=True)
    payload_preview = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.original_filename


class ImportRun(models.Model):
    tenant = models.ForeignKey("core.Tenant", on_delete=models.CASCADE, related_name="import_runs")
    data_source = models.ForeignKey(
        "core.DataSourceProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="import_runs",
    )
    source_document = models.ForeignKey(
        SourceDocument,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="import_runs",
    )
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    ingestion_mode = models.CharField(max_length=20, choices=IngestionMode.choices)
    status = models.CharField(max_length=32, choices=ImportStatus.choices)
    requested_by = models.CharField(max_length=120, default="System Seed")
    accepted_count = models.PositiveIntegerField(default=0)
    flagged_count = models.PositiveIntegerField(default=0)
    rejected_count = models.PositiveIntegerField(default=0)
    issue_count = models.PositiveIntegerField(default=0)
    summary = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return "{} / {}".format(self.tenant.slug, self.source_type)


class ImportIssue(models.Model):
    import_run = models.ForeignKey(ImportRun, on_delete=models.CASCADE, related_name="issues")
    severity = models.CharField(max_length=16, choices=IssueSeverity.choices)
    line_number = models.PositiveIntegerField(null=True, blank=True)
    field_name = models.CharField(max_length=120, blank=True)
    message = models.TextField()
    raw_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["import_run_id", "severity", "line_number", "id"]

    def __str__(self):
        return "{}: {}".format(self.severity, self.message)
