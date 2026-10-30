from django.db import connection
from django.test import TestCase
from django.urls import reverse


class AvailabilityTest(TestCase):
    """TC-AVAIL-01: Verify application availability."""

    def test_health_endpoint_returns_success(self):
        response = self.client.get(reverse("health_check"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "database": "ok"},
        )

    def test_database_connection_is_usable(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

        self.assertEqual(result[0], 1)
