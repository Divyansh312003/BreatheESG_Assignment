from django.db import models

from core.constants import AuditEventType


class AuditEvent(models.Model):
    tenant = models.ForeignKey("core.Tenant", on_delete=models.CASCADE, related_name="audit_events")
    import_run = models.ForeignKey(
        "ingestion.ImportRun",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    activity_record = models.ForeignKey(
        "core.ActivityRecord",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    actor = models.CharField(max_length=120, blank=True)
    event_type = models.CharField(max_length=32, choices=AuditEventType.choices)
    message = models.TextField()
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return "{} / {}".format(self.event_type, self.tenant.slug)
