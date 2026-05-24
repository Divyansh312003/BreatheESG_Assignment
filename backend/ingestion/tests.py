import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client, TestCase, override_settings

from core.models import Tenant


class MediaIsolationMixin:
    @classmethod
    def setUpClass(cls):
        cls._temp_media = tempfile.mkdtemp(prefix="breathe-esg-media-")
        cls._media_override = override_settings(MEDIA_ROOT=cls._temp_media)
        cls._media_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._media_override.disable()
        shutil.rmtree(cls._temp_media, ignore_errors=True)


class ImportWorkflowTests(MediaIsolationMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_data")

    def setUp(self):
        self.client = Client()
        self.tenant = Tenant.objects.get(slug="atlas-manufacturing")

    def test_sap_upload_creates_records_and_issues(self):
        sample_path = settings.PROJECT_ROOT / "sample_data" / "sap_export_demo.csv"
        upload = SimpleUploadedFile(
            "sap_export_demo.csv",
            sample_path.read_bytes(),
            content_type="text/csv",
        )

        response = self.client.post(
            "/api/v1/imports/sap",
            {"tenantId": self.tenant.id, "actor": "QA Analyst", "file": upload},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()["importRun"]
        self.assertGreaterEqual(payload["acceptedCount"], 4)
        self.assertGreaterEqual(payload["issueCount"], 2)

    def test_travel_sync_creates_scope_three_rows(self):
        response = self.client.post(
            "/api/v1/imports/travel-sync",
            data='{"tenantId": %s, "actor": "QA Analyst"}' % self.tenant.id,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()["importRun"]
        self.assertEqual(payload["sourceType"], "TRAVEL")
        self.assertGreaterEqual(payload["acceptedCount"], 3)
