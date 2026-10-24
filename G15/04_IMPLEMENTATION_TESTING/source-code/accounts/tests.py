
from django.test import TestCase
from django.urls import reverse
from django.conf import settings

from accounts.models import User
from categories.models import Category
from transactions.models import Transaction
from budgets.models import Budget, Alert
from recurring.models import RecurringRule
from accounts.forms import RegistrationForm, ProfileForm


class ProjectSetupTest(TestCase):
    def test_all_six_domain_models_are_available(self):
        """TC-MNT-01: Verify all six required domain models exist."""
        required_models = [
            User,
            Category,
            Transaction,
            Budget,
            RecurringRule,
            Alert,
        ]

        for model in required_models:
            with self.subTest(model=model.__name__):
                self.assertTrue(hasattr(model, "objects"))


class AuthenticationSecurityTest(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            email="customer@example.com",
            password="SecurePass123",
            name="Test Customer",
        )

    def test_session_timeout_is_30_minutes(self):
        self.assertEqual(settings.SESSION_COOKIE_AGE, 1800)
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)

    def test_password_is_hashed(self):
        self.assertNotEqual(
            self.customer.password,
            "SecurePass123",
        )
        self.assertTrue(
            self.customer.check_password("SecurePass123")
        )

    def test_registration_rejects_password_without_digit(self):
        form = RegistrationForm(
            data={
                "name": "Test User",
                "email": "newuser@example.com",
                "password1": "SecurePassword",
                "password2": "SecurePassword",
            }
        )
        self.assertFalse(form.is_valid())

    def test_registration_rejects_password_without_letter(self):
        form = RegistrationForm(
            data={
                "name": "Test User",
                "email": "newuser@example.com",
                "password1": "12345678",
                "password2": "12345678",
            }
        )
        self.assertFalse(form.is_valid())

    def test_customer_cannot_access_django_admin(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 302)

    def test_profile_form_cannot_change_role(self):
        form = ProfileForm(
            data={
                "name": "Updated Customer",
                "email": "customer@example.com",
                "role": "Administrator",
            },
            instance=self.customer,
        )
        self.assertTrue(form.is_valid())
        self.assertNotIn("role", form.fields)


class AuthenticationAcceptanceTests(TestCase):
    """Acceptance tests for FR-001 through FR-004."""

    def setUp(self):
        self.customer = User.objects.create_user(
            email="customer@example.com",
            password="SecurePass123",
            name="Test Customer",
        )

    def test_tc_auth_01_registration_and_duplicate_email(self):
        """FR-001: Registration succeeds; duplicate email is rejected."""
        registration_url = reverse("register")

        response = self.client.post(
            registration_url,
            {
                "name": "New Customer",
                "email": "newcustomer@example.com",
                "password1": "SecurePass123",
                "password2": "SecurePass123",
            },
        )

        self.assertRedirects(response, reverse("login"))

        new_user = User.objects.get(email="newcustomer@example.com")
        self.assertTrue(new_user.check_password("SecurePass123"))
        self.assertNotEqual(new_user.password, "SecurePass123")

        # Email matching must be case-insensitive.
        response = self.client.post(
            registration_url,
            {
                "name": "Duplicate Customer",
                "email": "NEWCUSTOMER@example.com",
                "password1": "SecurePass123",
                "password2": "SecurePass123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            User.objects.filter(
                email__iexact="newcustomer@example.com"
            ).count(),
            1,
        )

    def test_tc_auth_02_login_success_and_failure(self):
        """FR-002: Valid credentials authenticate; invalid ones do not."""
        login_url = reverse("login")

        response = self.client.post(
            login_url,
            {
                "email": "customer@example.com",
                "password": "SecurePass123",
            },
        )

        self.assertRedirects(response, reverse("home"))
        self.assertIn("_auth_user_id", self.client.session)

        # Start a separate anonymous session for the failed login.
        self.client.logout()

        response = self.client.post(
            login_url,
            {
                "email": "customer@example.com",
                "password": "WrongPassword123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

        messages = list(response.context["messages"])
        self.assertTrue(
            any(
                str(message) == "Invalid email or password."
                for message in messages
            )
        )

    def test_tc_auth_03_profile_name_update_and_empty_name(self):
        """FR-003: Name changes persist; an empty name is rejected."""
        self.client.force_login(self.customer)
        profile_url = reverse("profile")

        response = self.client.post(
            profile_url,
            {
                "name": "Updated Customer",
                "email": "customer@example.com",
            },
        )

        self.assertRedirects(response, profile_url)

        self.customer.refresh_from_db()
        self.assertEqual(self.customer.name, "Updated Customer")

        # Reloading the page must show the saved name.
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["form"].instance.name,
            "Updated Customer",
        )

        response = self.client.post(
            profile_url,
            {
                "name": "",
                "email": "customer@example.com",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())

        self.customer.refresh_from_db()
        self.assertEqual(self.customer.name, "Updated Customer")

    def test_tc_auth_04_logout_invalidates_session(self):
        """FR-004: Logout ends authentication and protects profile access."""
        self.client.force_login(self.customer)
        profile_url = reverse("profile")
        logout_url = reverse("logout")

        self.assertEqual(
            self.client.get(profile_url).status_code,
            200,
        )

        response = self.client.post(logout_url)
        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)

        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response.url.startswith(reverse("login") + "?")
            or response.url == reverse("login")
        )
