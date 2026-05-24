from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from core.constants import ActivityCategory, IngestionMode, ScopeCategory, SourceType
from core.models import DataSourceProfile, EmissionFactor, Facility, FacilityAlias, Tenant
from ingestion.services import process_import, sync_travel_demo


class Command(BaseCommand):
    help = "Seed demo tenants, facilities, source mappings, emission factors, and optional sample imports."

    def add_arguments(self, parser):
        parser.add_argument(
            "--load-samples",
            action="store_true",
            help="Import the bundled sample SAP, utility, and travel data after seeding reference data.",
        )

    def handle(self, *args, **options):
        primary_tenant, _ = Tenant.objects.update_or_create(
            slug="atlas-manufacturing",
            defaults={
                "name": "Atlas Manufacturing Group",
                "sector": "Industrial Manufacturing",
                "reporting_currency": "USD",
            },
        )
        Tenant.objects.update_or_create(
            slug="northwind-logistics",
            defaults={
                "name": "Northwind Logistics",
                "sector": "Distribution",
                "reporting_currency": "USD",
            },
        )

        facilities = [
            (primary_tenant, "PL01", "London Operations Hub", "GB", "London"),
            (primary_tenant, "DE02", "Munich Fabrication Hub", "DE", "Munich"),
        ]
        for tenant, code, name, country_code, city in facilities:
            Facility.objects.update_or_create(
                tenant=tenant,
                code=code,
                defaults={
                    "name": name,
                    "country_code": country_code,
                    "city": city,
                    "timezone": "UTC",
                },
            )

        london = Facility.objects.get(tenant=primary_tenant, code="PL01")
        munich = Facility.objects.get(tenant=primary_tenant, code="DE02")

        aliases = [
            (london, SourceType.SAP, "PL01"),
            (london, SourceType.UTILITY, "PL01"),
            (london, SourceType.UTILITY, "GB-PL01-UTILITY"),
            (london, SourceType.TRAVEL, "PL01"),
            (munich, SourceType.SAP, "DE02"),
            (munich, SourceType.UTILITY, "DE02"),
            (munich, SourceType.UTILITY, "DE02-ELEC-001"),
            (munich, SourceType.TRAVEL, "DE02"),
        ]
        for facility, source_type, alias in aliases:
            FacilityAlias.objects.update_or_create(
                facility=facility,
                source_type=source_type,
                alias=alias,
            )

        source_profiles = [
            (SourceType.SAP, "SAP MM Export", IngestionMode.FILE_UPLOAD, {"acceptedExtensions": [".csv"]}),
            (SourceType.UTILITY, "Green Button Utility Feed", IngestionMode.FILE_UPLOAD, {"acceptedExtensions": [".xml"]}),
            (SourceType.TRAVEL, "SAP Concur Travel Receipts", IngestionMode.API_PULL, {"demoFeed": True}),
        ]
        for source_type, label, ingestion_mode, config in source_profiles:
            DataSourceProfile.objects.update_or_create(
                tenant=primary_tenant,
                source_type=source_type,
                label=label,
                defaults={
                    "ingestion_mode": ingestion_mode,
                    "is_active": True,
                    "config": config,
                },
            )

        factors = [
            ("sap_fuel_diesel_liter", SourceType.SAP, ActivityCategory.FUEL, ScopeCategory.SCOPE_1, "L", "2.680000"),
            ("sap_fuel_gasoline_liter", SourceType.SAP, ActivityCategory.FUEL, ScopeCategory.SCOPE_1, "L", "2.310000"),
            ("sap_procurement_raw_material_spend_usd", SourceType.SAP, ActivityCategory.PROCUREMENT, ScopeCategory.SCOPE_3, "USD_SPEND", "0.440000"),
            ("sap_procurement_office_furniture_spend_usd", SourceType.SAP, ActivityCategory.PROCUREMENT, ScopeCategory.SCOPE_3, "USD_SPEND", "0.190000"),
            ("sap_procurement_generic_spend_usd", SourceType.SAP, ActivityCategory.PROCUREMENT, ScopeCategory.SCOPE_3, "USD_SPEND", "0.300000"),
            ("utility_electricity_grid_kwh", SourceType.UTILITY, ActivityCategory.ELECTRICITY, ScopeCategory.SCOPE_2, "KWH", "0.233000"),
            ("travel_air_mile", SourceType.TRAVEL, ActivityCategory.AIR_TRAVEL, ScopeCategory.SCOPE_3, "MILE", "0.180000"),
            ("travel_hotel_night", SourceType.TRAVEL, ActivityCategory.HOTEL, ScopeCategory.SCOPE_3, "ROOM_NIGHT", "14.000000"),
            ("travel_ground_mile", SourceType.TRAVEL, ActivityCategory.GROUND, ScopeCategory.SCOPE_3, "MILE", "0.320000"),
        ]
        for code, source_type, category, scope, base_unit, factor_value in factors:
            EmissionFactor.objects.update_or_create(
                code=code,
                defaults={
                    "source_type": source_type,
                    "category": category,
                    "scope": scope,
                    "base_unit": base_unit,
                    "kg_co2e_per_unit": factor_value,
                    "notes": "Prototype-only factor for demo review flows.",
                },
            )

        self.stdout.write(self.style.SUCCESS("Seeded tenants, facilities, aliases, source profiles, and factors."))

        if not options["load_samples"]:
            return

        sample_specs = [
            (SourceType.SAP, "sap_export_demo.csv", IngestionMode.FILE_UPLOAD),
            (SourceType.UTILITY, "utility_green_button_demo.xml", IngestionMode.FILE_UPLOAD),
        ]

        for source_type, file_name, ingestion_mode in sample_specs:
            if primary_tenant.activity_records.filter(source_type=source_type).exists():
                continue

            file_path = settings.PROJECT_ROOT / "sample_data" / file_name
            process_import(
                tenant=primary_tenant,
                source_type=source_type,
                ingestion_mode=ingestion_mode,
                actor="Seed Loader",
                file_name=file_name,
                file_bytes=Path(file_path).read_bytes(),
            )

        if not primary_tenant.activity_records.filter(source_type=SourceType.TRAVEL).exists():
            sync_travel_demo(primary_tenant, "Seed Loader")

        self.stdout.write(self.style.SUCCESS("Loaded bundled sample imports."))
