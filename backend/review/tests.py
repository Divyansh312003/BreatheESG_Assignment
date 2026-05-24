import shutil
import tempfile

from django.core.management import call_command
from django.test import Client, TestCase, override_settings

from core.models import ActivityRecord, Tenant

from .models import AuditEvent


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


class ReviewWorkflowTests(MediaIsolationMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_data", load_samples=True)

    def setUp(self):
        self.client = Client()
        self.tenant = Tenant.objects.get(slug="atlas-manufacturing")

    def test_review_endpoint_locks_record(self):
        record = ActivityRecord.objects.filter(tenant=self.tenant).first()
        response = self.client.post(
            f"/api/v1/records/{record.id}/review",
            data='{"reviewStatus": "APPROVED", "actor": "QA Analyst", "note": "Looks good."}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        record.refresh_from_db()
        self.assertEqual(record.review_status, "APPROVED")
        self.assertEqual(record.reviewed_by, "QA Analyst")
        self.assertIsNotNone(record.locked_at)
        self.assertTrue(
            AuditEvent.objects.filter(activity_record=record, event_type="RECORD_APPROVED").exists()
        )
