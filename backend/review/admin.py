from django.contrib import admin

from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("tenant", "event_type", "actor", "created_at")
    list_filter = ("tenant", "event_type")
    search_fields = ("actor", "message")

# Register your models here.
