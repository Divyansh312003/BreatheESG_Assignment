from django.contrib import admin

from .models import ActivityRecord, DataSourceProfile, EmissionFactor, Facility, FacilityAlias, Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "sector", "reporting_currency")
    search_fields = ("name", "slug")


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ("tenant", "code", "name", "country_code", "city")
    list_filter = ("tenant", "country_code")
    search_fields = ("tenant__name", "code", "name")


@admin.register(FacilityAlias)
class FacilityAliasAdmin(admin.ModelAdmin):
    list_display = ("facility", "source_type", "alias")
    list_filter = ("source_type",)
    search_fields = ("alias", "facility__code", "facility__name")


@admin.register(DataSourceProfile)
class DataSourceProfileAdmin(admin.ModelAdmin):
    list_display = ("tenant", "source_type", "label", "ingestion_mode", "is_active")
    list_filter = ("tenant", "source_type", "ingestion_mode", "is_active")
    search_fields = ("label", "tenant__name")


@admin.register(EmissionFactor)
class EmissionFactorAdmin(admin.ModelAdmin):
    list_display = ("code", "source_type", "category", "scope", "base_unit", "kg_co2e_per_unit")
    list_filter = ("source_type", "category", "scope")
    search_fields = ("code", "notes")


@admin.register(ActivityRecord)
class ActivityRecordAdmin(admin.ModelAdmin):
    list_display = (
        "tenant",
        "source_type",
        "category",
        "scope",
        "review_status",
        "facility",
        "activity_date",
        "estimated_kg_co2e",
    )
    list_filter = ("tenant", "source_type", "category", "scope", "review_status")
    search_fields = ("external_id", "description", "source_document_identifier")

# Register your models here.
