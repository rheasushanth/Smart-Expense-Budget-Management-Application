
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User, SecurityEvent
from categories.models import Category


class SecurityAcceptanceTests(TestCase):

    def setUp(self):
        self.customer = User.objects.create_user(
            email="customer@example.com",
            password="SecurePass123",
            name="Test Customer",
        )

        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="SecurePass123",
            name="Test Admin",
            role="Administrator",
            is_staff=True,
        )

    def test_tc_sec_06_01_failed_login_is_logged(self):
        self.client.post(
            reverse("login"),
            {
                "email": self.customer.email,
                "password": "WrongPassword123",
            },
        )

        self.assertTrue(
            SecurityEvent.objects.filter(
                event_type=SecurityEvent.EventType.FAILED_LOGIN,
                user=self.customer,
            ).exists()
        )

    def test_tc_sec_06_02_five_failures_lock_account(self):
        for _ in range(5):
            self.client.post(
                reverse("login"),
                {
                    "email": self.customer.email,
                    "password": "WrongPassword123",
                },
            )

        self.customer.refresh_from_db()

        self.assertEqual(self.customer.failed_login_attempts, 5)
        self.assertIsNotNone(self.customer.locked_until)
        self.assertGreater(self.customer.locked_until, timezone.now())

        self.assertTrue(
            SecurityEvent.objects.filter(
                event_type=SecurityEvent.EventType.ACCOUNT_LOCKED,
                user=self.customer,
            ).exists()
        )

    def test_tc_sec_06_03_locked_account_cannot_login(self):
        self.customer.locked_until = timezone.now() + timedelta(minutes=10)
        self.customer.failed_login_attempts = 5
        self.customer.save()

        response = self.client.post(
            reverse("login"),
            {
                "email": self.customer.email,
                "password": "SecurePass123",
            },
        )

        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertContains(response, "temporarily locked")

    def test_tc_sec_06_03b_lockout_is_not_revealed_without_the_password(self):
        """A wrong password must not disclose that an account is locked.

        Only a registered address can ever be locked, so answering a wrong
        password with "temporarily locked" would tell an attacker which
        email addresses exist (SEC-002, SRS 5.1.2). The reply has to match
        the one an unknown address gets.
        """
        self.customer.locked_until = timezone.now() + timedelta(minutes=10)
        self.customer.failed_login_attempts = 5
        self.customer.save()

        locked = self.client.post(
            reverse("login"),
            {
                "email": self.customer.email,
                "password": "WrongPassword123",
            },
        )
        unknown = self.client.post(
            reverse("login"),
            {
                "email": "nobody@example.com",
                "password": "WrongPassword123",
            },
        )

        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotContains(locked, "temporarily locked")
        self.assertContains(locked, "Invalid email or password.")
        self.assertContains(unknown, "Invalid email or password.")

    def test_tc_sec_06_04_expired_lockout_allows_login(self):
        self.customer.locked_until = timezone.now() - timedelta(seconds=1)
        self.customer.failed_login_attempts = 5
        self.customer.save()

        response = self.client.post(
            reverse("login"),
            {
                "email": self.customer.email,
                "password": "SecurePass123",
            },
        )

        self.assertRedirects(response, reverse("home"))
        self.assertIn("_auth_user_id", self.client.session)

        self.customer.refresh_from_db()
        self.assertEqual(self.customer.failed_login_attempts, 0)
        self.assertIsNone(self.customer.locked_until)

    def test_tc_sec_06_05_unauthorized_access_is_logged(self):
        self.client.force_login(self.customer)

        response = self.client.get(reverse("categories:list"))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            SecurityEvent.objects.filter(
                event_type=SecurityEvent.EventType.UNAUTHORIZED_ACCESS,
                user=self.customer,
            ).exists()
        )

    def test_tc_sec_06_06_admin_category_disable_is_logged(self):
        category = Category.objects.create(
            name="Test Expense",
            type="Expense",
            created_by=self.admin,
        )

        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("categories:disable", args=[category.pk])
        )

        self.assertRedirects(response, reverse("categories:list"))

        self.assertTrue(
            SecurityEvent.objects.filter(
                event_type=SecurityEvent.EventType.CATEGORY_STATUS_CHANGED,
                user=self.admin,
            ).exists()
        )

    def test_tc_sec_06_07_successful_login_resets_counter(self):
        self.customer.failed_login_attempts = 3
        self.customer.failed_login_window_started_at = timezone.now()
        self.customer.save()

        self.client.post(
            reverse("login"),
            {
                "email": self.customer.email,
                "password": "SecurePass123",
            },
        )

        self.customer.refresh_from_db()
        self.assertEqual(self.customer.failed_login_attempts, 0)
        self.assertIsNone(self.customer.locked_until)
        self.assertIsNone(self.customer.failed_login_window_started_at)

    def test_tc_sec_06_08_unknown_email_is_logged(self):
        self.client.post(
            reverse("login"),
            {
                "email": "unknown@example.com",
                "password": "WrongPassword123",
            },
        )

        self.assertTrue(
            SecurityEvent.objects.filter(
                event_type=SecurityEvent.EventType.FAILED_LOGIN,
                email="unknown@example.com",
                user__isnull=True,
            ).exists()
        )

    def test_tc_sec_06_09_anonymous_access_is_logged(self):
        response = self.client.get(reverse("categories:list"))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            SecurityEvent.objects.filter(
                event_type=SecurityEvent.EventType.UNAUTHORIZED_ACCESS,
                user__isnull=True,
            ).exists()
        )

    def test_tc_sec_06_10_five_failures_outside_window_do_not_lock(self):
        self.customer.failed_login_attempts = 4
        self.customer.failed_login_window_started_at = (
            timezone.now() - timedelta(minutes=11)
        )
        self.customer.save()

        self.client.post(
            reverse("login"),
            {
                "email": self.customer.email,
                "password": "WrongPassword123",
            },
        )

        self.customer.refresh_from_db()
        self.assertEqual(self.customer.failed_login_attempts, 1)
        self.assertIsNone(self.customer.locked_until)

    def test_tc_sec_06_11_category_creation_is_logged(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("categories:add"),
            {
                "name": "New Test Category",
                "type": "Expense",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            SecurityEvent.objects.filter(
                event_type=SecurityEvent.EventType.CATEGORY_CREATED,
                user=self.admin,
            ).exists()
        )

    def test_tc_sec_06_12_category_edit_is_logged(self):
        category = Category.objects.create(
            name="Old Category",
            type="Expense",
            created_by=self.admin,
        )

        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("categories:edit", args=[category.pk]),
            {
                "name": "Updated Category",
                "type": "Expense",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            SecurityEvent.objects.filter(
                event_type=SecurityEvent.EventType.CATEGORY_UPDATED,
                user=self.admin,
            ).exists()
        )

    def test_tc_sec_06_13_category_enable_is_logged(self):
        category = Category.objects.create(
            name="Disabled Category",
            type="Expense",
            created_by=self.admin,
            is_active=False,
        )

        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("categories:enable", args=[category.pk])
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            SecurityEvent.objects.filter(
                event_type=SecurityEvent.EventType.CATEGORY_STATUS_CHANGED,
                user=self.admin,
            ).exists()
        )
