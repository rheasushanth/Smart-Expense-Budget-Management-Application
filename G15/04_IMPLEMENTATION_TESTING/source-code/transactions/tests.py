
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from categories.models import Category
from transactions.models import Transaction


class RecordIncomeTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            email="manogna@example.com",
            password="TestPassword123!",
            name="Test User",
        )
        self.category = Category.objects.create(
            name="Salary",
            type=Category.CategoryType.INCOME,
            is_active=True,
            created_by=self.user,
        )
        self.client.login(
            email="manogna@example.com",
            password="TestPassword123!",
        )

    def test_user_can_record_income(self):
        response = self.client.post(
            reverse("record_income"),
            {
                "amount": "25000.00",
                "category": self.category.pk,
                "date": date.today().isoformat(),
                "note": "Monthly salary",
            },
        )

        self.assertRedirects(response, reverse("record_income"))
        transaction = Transaction.objects.get(
            user=self.user,
            type=Transaction.TransactionType.INCOME,
        )
        self.assertEqual(transaction.amount, Decimal("25000.00"))
        self.assertEqual(transaction.category, self.category)
        self.assertEqual(transaction.note, "Monthly salary")
        self.assertEqual(transaction.source, "Manual")

    def test_income_page_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("record_income"))
        self.assertEqual(response.status_code, 302)

    def test_expense_category_cannot_be_used_for_income(self):
        expense_category = Category.objects.create(
            name="Groceries",
            type=Category.CategoryType.EXPENSE,
            is_active=True,
            created_by=self.user,
        )

        response = self.client.post(
            reverse("record_income"),
            {
                "amount": "100.00",
                "category": expense_category.pk,
                "date": date.today().isoformat(),
                "note": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Transaction.objects.filter(
                user=self.user,
                category=expense_category,
                type=Transaction.TransactionType.INCOME,
            ).exists()
        )
