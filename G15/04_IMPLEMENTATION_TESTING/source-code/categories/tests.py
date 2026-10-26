
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Category


class CategoryAdminTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()

        cls.admin_user = User.objects.create_superuser(
            email="admin@example.com",
            password="TestPassword123!",
        )

        cls.category = Category.objects.create(
            name="Food",
            type=Category.CategoryType.EXPENSE,
            is_active=True,
            created_by=cls.admin_user,
        )

    def setUp(self):
        self.client.force_login(self.admin_user)

    def test_admin_can_add_category(self):
        response = self.client.post(
            reverse("admin:categories_category_add"),
            {
                "name": "Travel",
                "type": Category.CategoryType.EXPENSE,
                "is_active": True,
                "created_by": self.admin_user.pk,
                "_save": "Save",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Category.objects.filter(
                name="Travel",
                type=Category.CategoryType.EXPENSE,
            ).exists()
        )

    def test_admin_can_edit_category(self):
        response = self.client.post(
            reverse(
                "admin:categories_category_change",
                args=[self.category.pk],
            ),
            {
                "name": "Groceries",
                "type": Category.CategoryType.EXPENSE,
                "is_active": True,
                "created_by": self.admin_user.pk,
                "_save": "Save",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.category.refresh_from_db()
        self.assertEqual(self.category.name, "Groceries")

    def test_admin_can_disable_and_reenable_category(self):
        change_url = reverse(
            "admin:categories_category_change",
            args=[self.category.pk],
        )

        # Disable the category
        response = self.client.post(
            change_url,
            {
                "name": self.category.name,
                "type": self.category.type,
                "is_active": False,
                "created_by": self.admin_user.pk,
                "_save": "Save",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.category.refresh_from_db()
        self.assertFalse(self.category.is_active)

        # Re-enable the category
        response = self.client.post(
            change_url,
            {
                "name": self.category.name,
                "type": self.category.type,
                "is_active": True,
                "created_by": self.admin_user.pk,
                "_save": "Save",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.category.refresh_from_db()
        self.assertTrue(self.category.is_active)
