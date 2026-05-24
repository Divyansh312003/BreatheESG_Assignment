from django.db import models

from .constants import (
    ActivityCategory,
    IngestionMode,
    ReviewStatus,
    ScopeCategory,
    SourceType,
)


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Tenant(TimestampedModel):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    sector = models.CharField(max_length=80)
    reporting_currency = models.CharField(max_length=3, default="USD")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Facility(TimestampedModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="facilities")
    code = models.CharField(max_length=40)
    name = models.CharField(max_length=120)
    country_code = models.CharField(max_length=2)
    city = models.CharField(max_length=80)
    timezone = models.CharField(max_length=64, default="UTC")

    class Meta:
        ordering = ["tenant__name", "code"]
        unique_together = [["tenant", "code"]]

    def __str__(self):
        return "{} ({})".format(self.name, self.code)


class FacilityAlias(TimestampedModel):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="aliases")
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    alias = models.CharField(max_length=120)

    class Meta:
        ordering = ["facility__tenant__name", "alias"]
        unique_together = [["source_type", "alias"]]

    def __str__(self):
        return "{} -> {}".format(self.alias, self.facility.code)


class DataSourceProfile(TimestampedModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="data_sources")
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    label = models.CharField(max_length=120)
    ingestion_mode = models.CharField(max_length=20, choices=IngestionMode.choices)
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant__name", "source_type", "label"]
        unique_together = [["tenant", "source_type", "label"]]

    def __str__(self):
        return "{} / {}".format(self.tenant.slug, self.label)


class EmissionFactor(TimestampedModel):
    code = models.CharField(max_length=80, unique=True)
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    category = models.CharField(max_length=24, choices=ActivityCategory.choices)
    scope = models.CharField(max_length=16, choices=ScopeCategory.choices)
    base_unit = models.CharField(max_length=32)
    kg_co2e_per_unit = models.DecimalField(max_digits=14, decimal_places=6)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["source_type", "category", "code"]

    def __str__(self):
        return self.code


class ActivityRecord(TimestampedModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="activity_records")
    facility = models.ForeignKey(
        Facility,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_records",
    )
    data_source = models.ForeignKey(
        "core.DataSourceProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_records",
    )
    import_run = models.ForeignKey(
        "ingestion.ImportRun",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_records",
    )
    source_document = models.ForeignKey(
        "ingestion.SourceDocument",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_records",
    )
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    category = models.CharField(max_length=24, choices=ActivityCategory.choices)
    scope = models.CharField(max_length=16, choices=ScopeCategory.choices)
    review_status = models.CharField(
        max_length=16,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
    )
    external_id = models.CharField(max_length=120)
    source_line_number = models.PositiveIntegerField(null=True, blank=True)
    source_document_identifier = models.CharField(max_length=120)
    activity_date = models.DateField()
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    description = models.CharField(max_length=240)
    quantity_value = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    quantity_unit = models.CharField(max_length=32, blank=True)
    normalized_quantity = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        null=True,
        blank=True,
    )
    normalized_unit = models.CharField(max_length=32, blank=True)
    currency_code = models.CharField(max_length=3, blank=True)
    spend_amount = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    estimated_kg_co2e = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        null=True,
        blank=True,
    )
    suspicion_score = models.PositiveSmallIntegerField(default=0)
    suspicion_reasons = models.JSONField(default=list, blank=True)
    review_note = models.TextField(blank=True)
    reviewed_by = models.CharField(max_length=120, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    source_payload = models.JSONField(default=dict, blank=True)
    normalized_payload = models.JSONField(default=dict, blank=True)
    edited_fields = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        unique_together = [["tenant", "source_type", "external_id"]]

    def __str__(self):
        return "{} / {}".format(self.source_type, self.external_id)
