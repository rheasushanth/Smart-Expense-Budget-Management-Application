
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError

from budgets.models import Budget
from recurring.models import RecurringRule
from transactions.models import Transaction

from .models import Category


class CategoryManagementTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()

        # Application Administrator, not a Django superuser.
        cls.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="TestPassword123!",
            name="Category Administrator",
            role="Administrator",
            is_staff=False,
            is_superuser=False,
        )

        cls.customer = User.objects.create_user(
            email="customer@example.com",
            password="TestPassword123!",
            name="Test Customer",
            role="Customer",
            is_staff=False,
            is_superuser=False,
        )

        cls.category = Category.objects.create(
            name="Food",
            type=Category.CategoryType.EXPENSE,
            is_active=True,
            created_by=cls.admin_user,
        )

    def setUp(self):
        self.client.force_login(self.admin_user)

    def test_administrator_can_view_categories(self):
        response = self.client.get(reverse("categories:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Food")

    def test_administrator_can_add_category(self):
        response = self.client.post(
            reverse("categories:add"),
            {
                "name": "Travel",
                "type": Category.CategoryType.EXPENSE,
                "is_active": True,
            },
        )

        self.assertRedirects(response, reverse("categories:list"))
        category = Category.objects.get(name="Travel")
        self.assertEqual(category.created_by, self.admin_user)

    def test_administrator_can_edit_category(self):
        response = self.client.post(
            reverse(
                "categories:edit",
                args=[self.category.category_id],
            ),
            {
                "name": "Groceries",
                "type": Category.CategoryType.EXPENSE,
                "is_active": True,
            },
        )

        self.assertRedirects(response, reverse("categories:list"))
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, "Groceries")

    def test_administrator_can_disable_and_reenable_category(self):
        disable_url = reverse(
            "categories:disable",
            args=[self.category.category_id],
        )
        enable_url = reverse(
            "categories:enable",
            args=[self.category.category_id],
        )

        response = self.client.post(disable_url)
        self.assertRedirects(response, reverse("categories:list"))

        self.category.refresh_from_db()
        self.assertFalse(self.category.is_active)

        response = self.client.post(enable_url)
        self.assertRedirects(response, reverse("categories:list"))

        self.category.refresh_from_db()
        self.assertTrue(self.category.is_active)

    def test_customer_receives_403_for_category_management(self):
        self.client.force_login(self.customer)

        urls = [
            reverse("categories:list"),
            reverse("categories:add"),
            reverse("categories:edit", args=[self.category.category_id]),
            reverse("categories:disable", args=[self.category.category_id]),
            reverse("categories:enable", args=[self.category.category_id]),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)

class DisabledCategoryAssignmentTest(TestCase):
    """TC-ADM-02: Disabled categories cannot be assigned to new records."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()

        cls.user = User.objects.create_user(
            email="fr021@example.com",
            password="TestPassword123!",
            name="FR021 Test User",
            role="Customer",
        )

        cls.admin = User.objects.create_user(
            email="fr021-admin@example.com",
            password="TestPassword123!",
            name="FR021 Test Administrator",
            role="Administrator",
        )

        cls.disabled_category = Category.objects.create(
            name="Disabled Food",
            type=Category.CategoryType.EXPENSE,
            is_active=False,
            created_by=cls.admin,
        )

    def test_disabled_category_cannot_be_assigned_to_new_transaction(self):
        with self.assertRaises(ValidationError):
            Transaction.objects.create(
                user=self.user,
                category=self.disabled_category,
                amount=Decimal("100.00"),
                type=Transaction.TransactionType.EXPENSE,
                date=date(2026, 10, 28),
            )

        self.assertFalse(
            Transaction.objects.filter(
                user=self.user,
                category=self.disabled_category,
            ).exists()
        )

    def test_disabled_category_cannot_be_assigned_to_new_budget(self):
        with self.assertRaises(ValidationError):
            Budget.objects.create(
                user=self.user,
                category=self.disabled_category,
                period=Budget.Period.MONTHLY,
                start_date=date(2026, 10, 1),
                limit_amount=Decimal("5000.00"),
            )

        self.assertFalse(
            Budget.objects.filter(
                user=self.user,
                category=self.disabled_category,
            ).exists()
        )

    def test_disabled_category_cannot_be_assigned_to_new_recurring_rule(self):
        with self.assertRaises(ValidationError):
            RecurringRule.objects.create(
                user=self.user,
                category=self.disabled_category,
                amount=Decimal("250.00"),
                frequency=RecurringRule.Frequency.MONTHLY,
                next_run_date=date(2026, 11, 1),
            )

        self.assertFalse(
            RecurringRule.objects.filter(
                user=self.user,
                category=self.disabled_category,
            ).exists()
        )

class RegisteredUsersAdminTest(TestCase):
    """TC-ADM-03: Administrator can view registered users."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()

        cls.admin_user = User.objects.create_superuser(
            email="fr022-admin@example.com",
            password="TestPassword123!",
            name="FR022 Administrator",
        )

        cls.registered_user = User.objects.create_user(
            email="fr022-customer@example.com",
            password="TestPassword123!",
            name="FR022 Registered Customer",
            role="Customer",
        )

    def setUp(self):
        self.client.force_login(self.admin_user)

    def test_administrator_can_view_registered_users(self):
        response = self.client.get(
            reverse("admin:accounts_user_changelist")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "FR022 Registered Customer")
        self.assertContains(response, "fr022-customer@example.com")
        self.assertContains(response, "FR022 Administrator")
