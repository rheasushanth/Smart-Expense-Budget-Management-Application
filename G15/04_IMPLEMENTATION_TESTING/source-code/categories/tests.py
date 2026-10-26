
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

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
