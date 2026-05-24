from django.db import models


class SourceType(models.TextChoices):
    SAP = "SAP", "SAP Export"
    UTILITY = "UTILITY", "Utility Feed"
    TRAVEL = "TRAVEL", "Corporate Travel API"


class IngestionMode(models.TextChoices):
    FILE_UPLOAD = "FILE_UPLOAD", "File Upload"
    API_PULL = "API_PULL", "API Pull"


class ScopeCategory(models.TextChoices):
    SCOPE_1 = "SCOPE_1", "Scope 1"
    SCOPE_2 = "SCOPE_2", "Scope 2"
    SCOPE_3 = "SCOPE_3", "Scope 3"


class ActivityCategory(models.TextChoices):
    FUEL = "FUEL", "Fuel Combustion"
    PROCUREMENT = "PROCUREMENT", "Purchased Goods"
    ELECTRICITY = "ELECTRICITY", "Purchased Electricity"
    AIR_TRAVEL = "AIR_TRAVEL", "Air Travel"
    HOTEL = "HOTEL", "Hotel Stay"
    GROUND = "GROUND", "Ground Transport"


class ReviewStatus(models.TextChoices):
    PENDING = "PENDING", "Pending Review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class ImportStatus(models.TextChoices):
    PROCESSING = "PROCESSING", "Processing"
    COMPLETED = "COMPLETED", "Completed"
    COMPLETED_WITH_ISSUES = "COMPLETED_WITH_ISSUES", "Completed With Issues"
    FAILED = "FAILED", "Failed"


class IssueSeverity(models.TextChoices):
    ERROR = "ERROR", "Error"
    WARNING = "WARNING", "Warning"


class AuditEventType(models.TextChoices):
    IMPORT_STARTED = "IMPORT_STARTED", "Import Started"
    IMPORT_COMPLETED = "IMPORT_COMPLETED", "Import Completed"
    IMPORT_FAILED = "IMPORT_FAILED", "Import Failed"
    RECORD_APPROVED = "RECORD_APPROVED", "Record Approved"
    RECORD_REJECTED = "RECORD_REJECTED", "Record Rejected"
