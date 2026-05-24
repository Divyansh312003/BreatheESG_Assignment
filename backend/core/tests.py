import shutil
import tempfile

from django.core.management import call_command
from django.test import Client, TestCase, override_settings

from .models import Tenant


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


class DashboardTests(MediaIsolationMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_data", load_samples=True)

    def setUp(self):
        self.client = Client()
        self.tenant = Tenant.objects.get(slug="atlas-manufacturing")

    def test_health_endpoint_reports_version(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertIn("version", payload)

    def test_dashboard_returns_seeded_records(self):
        response = self.client.get("/api/v1/dashboard", {"tenantId": self.tenant.id})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertGreater(payload["summary"]["totalRecords"], 0)
        self.assertGreater(len(payload["records"]), 0)
        self.assertGreater(len(payload["imports"]), 0)
