from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from budgets.models import Budget
from categories.models import Category
from transactions.models import Transaction

from .queries import budget_adherence, category_report, month_bounds


class ReportTestData(TestCase):
    """Fixtures for TC-RPT-01: Food 1000, Rent 3000, Travel 1000.

    The period is the current month so the Food budget counts as active
    (SRS Appendix A: a budget whose period has not yet ended).
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="asha@test.com", password="Str0ng#Pass1", name="Asha"
        )
        cls.admin = User.objects.create_user(
            email="admin@test.com",
            password="Str0ng#Pass1",
            name="Admin",
            role=User.Role.ADMINISTRATOR,
        )
        cls.food = Category.objects.create(
            name="Food", type=Category.CategoryType.EXPENSE, created_by=cls.admin
        )
        cls.rent = Category.objects.create(
            name="Rent", type=Category.CategoryType.EXPENSE, created_by=cls.admin
        )
        cls.travel = Category.objects.create(
            name="Travel", type=Category.CategoryType.EXPENSE, created_by=cls.admin
        )
        cls.salary = Category.objects.create(
            name="Salary", type=Category.CategoryType.INCOME, created_by=cls.admin
        )
        cls.start, cls.end = month_bounds()

    def spend(self, category, amount, when=None, user=None):
        return Transaction.objects.create(
            user=user or self.user,
            category=category,
            amount=Decimal(amount),
            type=Transaction.TransactionType.EXPENSE,
            date=when or self.start,
            note="",
        )

    def seed_the_month(self):
        self.spend(self.food, "1000.00")
        self.spend(self.rent, "3000.00")
        self.spend(self.travel, "1000.00")


class TCRPT01CategoryReport(ReportTestData):
    """TC-RPT-01, first half: Food 20%, Rent 60%, Travel 20%, total 5000."""

    def test_shares_and_total_match_the_seeded_month(self):
        self.seed_the_month()

        report = category_report(self.user, self.start, self.end)
        shares = {row["category"]: row["percentage"] for row in report["rows"]}

        self.assertEqual(report["total"], Decimal("5000.00"))
        self.assertEqual(shares["Food"], Decimal("20.0"))
        self.assertEqual(shares["Rent"], Decimal("60.0"))
        self.assertEqual(shares["Travel"], Decimal("20.0"))

    def test_rows_are_ordered_by_spend(self):
        self.seed_the_month()
        report = category_report(self.user, self.start, self.end)
        self.assertEqual(
            [row["category"] for row in report["rows"]],
            ["Rent", "Food", "Travel"],
        )

    def test_empty_month_reports_zero_without_error(self):
        report = category_report(self.user, self.start, self.end)
        self.assertEqual(report["rows"], [])
        self.assertEqual(report["total"], Decimal("0.00"))

    def test_income_is_not_counted(self):
        self.seed_the_month()
        Transaction.objects.create(
            user=self.user,
            category=self.salary,
            amount=Decimal("20000.00"),
            type=Transaction.TransactionType.INCOME,
            date=self.start,
            note="",
        )
        report = category_report(self.user, self.start, self.end)
        self.assertEqual(report["total"], Decimal("5000.00"))

    def test_other_users_spend_is_not_counted(self):
        self.seed_the_month()
        other = User.objects.create_user(
            email="bob@test.com", password="Str0ng#Pass1", name="Bob"
        )
        self.spend(self.food, "9999.00", user=other)

        report = category_report(self.user, self.start, self.end)
        self.assertEqual(report["total"], Decimal("5000.00"))

    def test_spend_outside_the_period_is_not_counted(self):
        self.seed_the_month()
        self.spend(self.food, "777.00", when=date(2020, 1, 15))

        report = category_report(self.user, self.start, self.end)
        self.assertEqual(report["total"], Decimal("5000.00"))

    def test_shares_sum_to_one_hundred(self):
        self.seed_the_month()
        report = category_report(self.user, self.start, self.end)
        self.assertEqual(
            sum(row["percentage"] for row in report["rows"]),
            Decimal("100.0"),
        )


class TCRPT01BudgetAdherence(ReportTestData):
    """TC-RPT-01, second half: Food budget 5000, spent 1000, remaining 4000."""

    def setUp(self):
        self.budget = Budget(
            user=self.user,
            category=self.food,
            period=Budget.Period.MONTHLY,
            start_date=self.start,
            limit_amount=Decimal("5000.00"),
        )
        self.budget.full_clean()
        self.budget.save()

    def test_limit_spent_and_remaining(self):
        self.spend(self.food, "1000.00")

        row = budget_adherence(self.user)[0]

        self.assertEqual(row["category"], "Food")
        self.assertEqual(row["limit"], Decimal("5000.00"))
        self.assertEqual(row["spent"], Decimal("1000.00"))
        self.assertEqual(row["remaining"], Decimal("4000.00"))
        self.assertEqual(row["percentage"], Decimal("20.0"))
        self.assertFalse(row["over_limit"])

    def test_untouched_budget_shows_full_remaining(self):
        row = budget_adherence(self.user)[0]
        self.assertEqual(row["spent"], Decimal("0.00"))
        self.assertEqual(row["remaining"], Decimal("5000.00"))

    def test_over_limit_is_flagged_with_negative_remaining(self):
        self.spend(self.food, "6000.00")
        row = budget_adherence(self.user)[0]
        self.assertTrue(row["over_limit"])
        self.assertEqual(row["remaining"], Decimal("-1000.00"))

    def test_expired_budgets_are_excluded(self):
        """Only active budgets appear — those whose period has not ended."""
        old = Budget(
            user=self.user,
            category=self.rent,
            period=Budget.Period.MONTHLY,
            start_date=date(2020, 1, 1),
            limit_amount=Decimal("3000.00"),
        )
        old.full_clean()
        old.save()

        categories = [row["category"] for row in budget_adherence(self.user)]
        self.assertIn("Food", categories)
        self.assertNotIn("Rent", categories)

    def test_another_users_budget_is_excluded(self):
        other = User.objects.create_user(
            email="bob@test.com", password="Str0ng#Pass1", name="Bob"
        )
        theirs = Budget(
            user=other,
            category=self.travel,
            period=Budget.Period.MONTHLY,
            start_date=self.start,
            limit_amount=Decimal("500.00"),
        )
        theirs.full_clean()
        theirs.save()

        categories = [row["category"] for row in budget_adherence(self.user)]
        self.assertNotIn("Travel", categories)


class ReportPage(ReportTestData):
    """The report page itself (FR-017, UC-04)."""

    def setUp(self):
        self.client.force_login(self.user)

    def test_page_renders_both_reports(self):
        self.seed_the_month()
        budget = Budget(
            user=self.user,
            category=self.food,
            period=Budget.Period.MONTHLY,
            start_date=self.start,
            limit_amount=Decimal("5000.00"),
        )
        budget.full_clean()
        budget.save()

        response = self.client.get(reverse("report"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["spending"]["total"], Decimal("5000.00"))
        self.assertEqual(len(response.context["adherence"]), 1)
        self.assertContains(response, "Spending by category")
        self.assertContains(response, "Budget adherence")
        self.assertContains(response, "60.0%")

    def test_empty_month_renders_without_error(self):
        response = self.client.get(reverse("report"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["spending"]["total"], Decimal("0.00"))

    def test_period_can_be_chosen(self):
        self.spend(self.food, "1000.00", when=date(2024, 3, 10))

        response = self.client.get(
            reverse("report"),
            {"start_date": "2024-03-01", "end_date": "2024-03-31"},
        )

        self.assertEqual(response.context["spending"]["total"], Decimal("1000.00"))

    def test_start_after_end_is_rejected(self):
        response = self.client.get(
            reverse("report"),
            {"start_date": "2024-03-31", "end_date": "2024-03-01"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "must not be after")

    def test_page_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("report"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.headers["Location"])
