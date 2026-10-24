from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from categories.models import Category
from transactions.models import Transaction

from .models import Budget
from .services import percentage_used, remaining_for, spend_for


class BudgetTestData(TestCase):
    """Shared fixtures: one user plus the categories TC-BUD-01 needs."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="asha@test.com",
            password="Str0ng#Pass1",
            name="Asha",
        )
        cls.admin = User.objects.create_user(
            email="admin@test.com",
            password="Str0ng#Pass1",
            name="Admin",
            role=User.Role.ADMINISTRATOR,
        )
        cls.food = Category.objects.create(
            name="Food",
            type=Category.CategoryType.EXPENSE,
            created_by=cls.admin,
        )
        cls.travel = Category.objects.create(
            name="Travel",
            type=Category.CategoryType.EXPENSE,
            created_by=cls.admin,
        )
        cls.salary = Category.objects.create(
            name="Salary",
            type=Category.CategoryType.INCOME,
            created_by=cls.admin,
        )

    def make_budget(self, **overrides):
        values = {
            "user": self.user,
            "category": self.food,
            "period": Budget.Period.MONTHLY,
            "start_date": date(2026, 10, 1),
            "limit_amount": Decimal("5000.00"),
        }
        values.update(overrides)
        return Budget(**values)


class TCBUD01CreateEditDelete(BudgetTestData):
    """TC-BUD-01 (FR-012): create, edit and delete budgets, and reject
    limit 0, threshold 101 and a budget on an Income category."""

    def setUp(self):
        self.client.force_login(self.user)

    def test_monthly_budget_is_saved_with_default_threshold(self):
        response = self.client.post(
            reverse("budget_create"),
            {
                "category": self.food.pk,
                "period": Budget.Period.MONTHLY,
                "start_date": "2026-10-01",
                "limit_amount": "5000.00",
                "threshold_pct": "80",
            },
        )

        self.assertRedirects(response, reverse("budget_list"))
        budget = Budget.objects.get(category=self.food)
        self.assertEqual(budget.limit_amount, Decimal("5000.00"))
        self.assertEqual(budget.threshold_pct, 80)
        self.assertEqual(budget.period, Budget.Period.MONTHLY)
        self.assertEqual(budget.user, self.user)

    def test_threshold_defaults_to_80_on_the_model(self):
        budget = self.make_budget()
        budget.full_clean()
        budget.save()
        self.assertEqual(budget.threshold_pct, 80)

    def test_weekly_budget_can_be_edited_then_deleted(self):
        self.client.post(
            reverse("budget_create"),
            {
                "category": self.travel.pk,
                "period": Budget.Period.WEEKLY,
                "start_date": "2026-11-02",
                "limit_amount": "3000.00",
                "threshold_pct": "80",
            },
        )
        budget = Budget.objects.get(category=self.travel)

        self.client.post(
            reverse("budget_edit", args=[budget.pk]),
            {
                "category": self.travel.pk,
                "period": Budget.Period.WEEKLY,
                "start_date": "2026-11-02",
                "limit_amount": "2000.00",
                "threshold_pct": "80",
            },
        )
        budget.refresh_from_db()
        self.assertEqual(budget.limit_amount, Decimal("2000.00"))

        self.client.post(reverse("budget_delete", args=[budget.pk]))
        self.assertFalse(Budget.objects.filter(pk=budget.pk).exists())

    def test_limit_of_zero_is_rejected(self):
        budget = self.make_budget(limit_amount=Decimal("0.00"))
        with self.assertRaises(ValidationError) as caught:
            budget.full_clean()
        self.assertIn("limit_amount", caught.exception.message_dict)

    def test_threshold_of_101_is_rejected(self):
        budget = self.make_budget(threshold_pct=101)
        with self.assertRaises(ValidationError) as caught:
            budget.full_clean()
        self.assertIn("threshold_pct", caught.exception.message_dict)

    def test_budget_on_an_income_category_is_rejected(self):
        budget = self.make_budget(category=self.salary)
        with self.assertRaises(ValidationError) as caught:
            budget.full_clean()
        self.assertIn("category", caught.exception.message_dict)

    def test_income_categories_are_not_offered_in_the_form(self):
        response = self.client.get(reverse("budget_create"))
        choices = response.context["form"].fields["category"].queryset
        self.assertIn(self.food, choices)
        self.assertNotIn(self.salary, choices)

    def test_delete_page_asks_for_confirmation_before_deleting(self):
        budget = self.make_budget()
        budget.save()

        response = self.client.get(reverse("budget_delete", args=[budget.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Delete budget")
        self.assertTrue(Budget.objects.filter(pk=budget.pk).exists())

    def test_a_user_cannot_edit_another_users_budget(self):
        budget = self.make_budget()
        budget.save()

        other = User.objects.create_user(
            email="bob@test.com", password="Str0ng#Pass1", name="Bob"
        )
        self.client.force_login(other)

        response = self.client.get(reverse("budget_edit", args=[budget.pk]))
        self.assertEqual(response.status_code, 404)


class TCBUD03OverlapRule(BudgetTestData):
    """TC-BUD-03 (FR-014): reject a second budget for the same category whose
    period overlaps an existing one; allow a non-overlapping period."""

    def test_second_monthly_budget_for_the_same_month_is_rejected(self):
        first = self.make_budget(start_date=date(2026, 10, 1))
        first.full_clean()
        first.save()

        clash = self.make_budget(start_date=date(2026, 10, 1))
        with self.assertRaises(ValidationError) as caught:
            clash.full_clean()
        self.assertIn("start_date", caught.exception.message_dict)

    def test_budget_for_the_following_month_is_accepted(self):
        first = self.make_budget(start_date=date(2026, 10, 1))
        first.full_clean()
        first.save()

        following = self.make_budget(start_date=date(2026, 11, 1))
        following.full_clean()
        following.save()

        self.assertEqual(Budget.objects.filter(category=self.food).count(), 2)

    def test_a_weekly_budget_inside_a_monthly_one_is_rejected(self):
        monthly = self.make_budget(start_date=date(2026, 10, 1))
        monthly.full_clean()
        monthly.save()

        weekly = self.make_budget(
            period=Budget.Period.WEEKLY,
            start_date=date(2026, 10, 12),
        )
        with self.assertRaises(ValidationError):
            weekly.full_clean()

    def test_same_period_for_a_different_category_is_allowed(self):
        food_budget = self.make_budget(start_date=date(2026, 10, 1))
        food_budget.full_clean()
        food_budget.save()

        travel_budget = self.make_budget(
            category=self.travel,
            start_date=date(2026, 10, 1),
        )
        travel_budget.full_clean()
        travel_budget.save()

        self.assertEqual(Budget.objects.count(), 2)

    def test_editing_a_budget_does_not_clash_with_itself(self):
        budget = self.make_budget(start_date=date(2026, 10, 1))
        budget.full_clean()
        budget.save()

        budget.limit_amount = Decimal("7000.00")
        budget.full_clean()
        budget.save()

        budget.refresh_from_db()
        self.assertEqual(budget.limit_amount, Decimal("7000.00"))


class BudgetPeriodEnd(BudgetTestData):
    """Period rule from SRS Appendix B.3."""

    def test_weekly_period_covers_seven_days(self):
        budget = self.make_budget(
            period=Budget.Period.WEEKLY,
            start_date=date(2026, 10, 1),
        )
        self.assertEqual(budget.period_end, date(2026, 10, 7))

    def test_monthly_period_ends_the_day_before_the_same_day_of_month(self):
        budget = self.make_budget(start_date=date(2026, 9, 15))
        self.assertEqual(budget.period_end, date(2026, 10, 14))

    def test_monthly_period_falls_back_to_the_last_day_of_a_short_month(self):
        budget = self.make_budget(start_date=date(2027, 1, 31))
        self.assertEqual(budget.period_end, date(2027, 2, 28))

    def test_monthly_period_rolls_over_the_year_end(self):
        budget = self.make_budget(start_date=date(2026, 12, 10))
        self.assertEqual(budget.period_end, date(2027, 1, 9))


class TCBUD02SpendTracking(BudgetTestData):
    """TC-BUD-02 (FR-013): cumulative Expense spend against a budget.

    With a Food budget of 5000, adding expenses of 1000 and 1500 and then
    deleting the 1000 one shows 1000, then 2500, then 1500. Income is never
    counted.
    """

    def setUp(self):
        self.budget = self.make_budget(start_date=date(2026, 10, 1))
        self.budget.full_clean()
        self.budget.save()

    def add_expense(self, amount, category=None, when=date(2026, 10, 5)):
        return Transaction.objects.create(
            user=self.user,
            category=category or self.food,
            amount=Decimal(amount),
            type=Transaction.TransactionType.EXPENSE,
            date=when,
            note="",
        )

    def test_spend_is_zero_before_any_transaction(self):
        self.assertEqual(spend_for(self.budget), Decimal("0.00"))

    def test_spend_accumulates_then_drops_when_a_transaction_is_deleted(self):
        first = self.add_expense("1000.00")
        self.assertEqual(spend_for(self.budget), Decimal("1000.00"))

        self.add_expense("1500.00")
        self.assertEqual(spend_for(self.budget), Decimal("2500.00"))

        first.delete()
        self.assertEqual(spend_for(self.budget), Decimal("1500.00"))

    def test_income_is_not_counted(self):
        self.add_expense("1000.00")
        Transaction.objects.create(
            user=self.user,
            category=self.salary,
            amount=Decimal("20000.00"),
            type=Transaction.TransactionType.INCOME,
            date=date(2026, 10, 5),
            note="",
        )
        self.assertEqual(spend_for(self.budget), Decimal("1000.00"))

    def test_another_category_is_not_counted(self):
        self.add_expense("1000.00")
        self.add_expense("800.00", category=self.travel)
        self.assertEqual(spend_for(self.budget), Decimal("1000.00"))

    def test_another_users_spend_is_not_counted(self):
        self.add_expense("1000.00")
        other = User.objects.create_user(
            email="bob@test.com", password="Str0ng#Pass1", name="Bob"
        )
        Transaction.objects.create(
            user=other,
            category=self.food,
            amount=Decimal("9999.00"),
            type=Transaction.TransactionType.EXPENSE,
            date=date(2026, 10, 5),
            note="",
        )
        self.assertEqual(spend_for(self.budget), Decimal("1000.00"))

    def test_transactions_outside_the_budget_period_are_not_counted(self):
        self.add_expense("1000.00", when=date(2026, 10, 1))
        self.add_expense("500.00", when=date(2026, 10, 31))
        self.add_expense("777.00", when=date(2026, 9, 30))
        self.add_expense("888.00", when=date(2026, 11, 1))

        self.assertEqual(self.budget.period_end, date(2026, 10, 31))
        self.assertEqual(spend_for(self.budget), Decimal("1500.00"))

    def test_remaining_and_percentage(self):
        self.add_expense("1000.00")
        self.assertEqual(remaining_for(self.budget), Decimal("4000.00"))
        self.assertEqual(percentage_used(self.budget), Decimal("20.0"))

    def test_remaining_goes_negative_once_the_limit_is_passed(self):
        self.add_expense("6000.00")
        self.assertEqual(remaining_for(self.budget), Decimal("-1000.00"))
        self.assertEqual(percentage_used(self.budget), Decimal("120.0"))

    def test_budget_list_shows_spend_remaining_and_percentage(self):
        self.add_expense("1000.00")
        self.client.force_login(self.user)

        response = self.client.get(reverse("budget_list"))

        self.assertEqual(response.status_code, 200)
        row = response.context["rows"][0]
        self.assertEqual(row["spent"], Decimal("1000.00"))
        self.assertEqual(row["remaining"], Decimal("4000.00"))
        self.assertEqual(row["percentage"], Decimal("20.0"))
        self.assertContains(response, "1000.00")
