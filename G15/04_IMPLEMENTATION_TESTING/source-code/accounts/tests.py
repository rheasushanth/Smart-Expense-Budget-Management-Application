
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
    def test_session_timeout_is_30_minutes(self):
        self.assertEqual(settings.SESSION_COOKIE_AGE, 1800)
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)
    def setUp(self):
        self.customer = User.objects.create_user(
            email="customer@example.com",
            password="SecurePass123",
            name="Test Customer",
        )

    def test_password_is_hashed(self):
        self.assertNotEqual(
            self.customer.password,
            "SecurePass123",
        )
        self.assertTrue(
            self.customer.check_password("SecurePass123")
        )

    def test_registration_rejects_password_without_digit(self):
        form = RegistrationForm(data={
            "name": "Test User",
            "email": "newuser@example.com",
            "password1": "SecurePassword",
            "password2": "SecurePassword",
        })
        self.assertFalse(form.is_valid())

    def test_registration_rejects_password_without_letter(self):
        form = RegistrationForm(data={
            "name": "Test User",
            "email": "newuser@example.com",
            "password1": "12345678",
            "password2": "12345678",
        })
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
