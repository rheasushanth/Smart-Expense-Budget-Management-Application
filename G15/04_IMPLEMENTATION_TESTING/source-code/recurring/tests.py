from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from categories.models import Category

from .models import RecurringRule
from .tasks import generate_due_transactions, get_next_run_date


class RecurringTestData(TestCase):
    """Fixtures for TC-REC-01."""

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
        cls.subscriptions = Category.objects.create(
            name="Subscriptions",
            type=Category.CategoryType.EXPENSE,
            created_by=cls.admin,
        )
        cls.salary = Category.objects.create(
            name="Salary",
            type=Category.CategoryType.INCOME,
            created_by=cls.admin,
        )
        cls.disabled = Category.objects.create(
            name="Old Gym",
            type=Category.CategoryType.EXPENSE,
            is_active=False,
            created_by=cls.admin,
        )

    def setUp(self):
        self.tomorrow = date.today() + timedelta(days=1)
        self.client.force_login(self.user)

    def make_rule(self, **overrides):
        values = {
            "user": self.user,
            "category": self.subscriptions,
            "amount": Decimal("999.00"),
            "frequency": RecurringRule.Frequency.MONTHLY,
            "next_run_date": self.tomorrow,
        }
        values.update(overrides)
        return RecurringRule(**values)

    def post_rule(self, url, **overrides):
        data = {
            "category": self.subscriptions.pk,
            "amount": "999.00",
            "frequency": RecurringRule.Frequency.MONTHLY,
            "next_run_date": self.tomorrow.isoformat(),
        }
        data.update(overrides)
        return self.client.post(url, data)


class TCREC01ConfigureEditDeactivate(RecurringTestData):
    """TC-REC-01 (FR-019).

    Create a monthly rule: amount 999, category Subscriptions, next run date
    tomorrow. Edit the amount to 1099. Then deactivate the rule. A disabled
    category or amount of 0 is rejected on create and on edit. After
    deactivation the rule shows as inactive.
    """

    def test_rule_is_saved_and_active(self):
        response = self.post_rule(reverse("rule_create"))

        self.assertRedirects(response, reverse("rule_list"))
        rule = RecurringRule.objects.get()
        self.assertEqual(rule.amount, Decimal("999.00"))
        self.assertEqual(rule.category, self.subscriptions)
        self.assertEqual(rule.frequency, RecurringRule.Frequency.MONTHLY)
        self.assertEqual(rule.next_run_date, self.tomorrow)
        self.assertEqual(rule.user, self.user)
        self.assertTrue(rule.is_active)

    def test_amount_can_be_edited(self):
        self.post_rule(reverse("rule_create"))
        rule = RecurringRule.objects.get()

        self.post_rule(reverse("rule_edit", args=[rule.pk]), amount="1099.00")

        rule.refresh_from_db()
        self.assertEqual(rule.amount, Decimal("1099.00"))

    def test_rule_shows_as_inactive_after_deactivation(self):
        self.post_rule(reverse("rule_create"))
        rule = RecurringRule.objects.get()
        self.assertTrue(rule.is_active)

        response = self.client.post(reverse("rule_deactivate", args=[rule.pk]))

        self.assertRedirects(response, reverse("rule_list"))
        rule.refresh_from_db()
        self.assertFalse(rule.is_active)

    def test_deactivation_keeps_the_rule_rather_than_deleting_it(self):
        self.post_rule(reverse("rule_create"))
        rule = RecurringRule.objects.get()

        self.client.post(reverse("rule_deactivate", args=[rule.pk]))

        self.assertTrue(RecurringRule.objects.filter(pk=rule.pk).exists())

    def test_amount_of_zero_is_rejected_on_create(self):
        rule = self.make_rule(amount=Decimal("0.00"))
        with self.assertRaises(ValidationError) as caught:
            rule.full_clean()
        self.assertIn("amount", caught.exception.message_dict)

        self.post_rule(reverse("rule_create"), amount="0.00")
        self.assertEqual(RecurringRule.objects.count(), 0)

    def test_amount_of_zero_is_rejected_on_edit(self):
        self.post_rule(reverse("rule_create"))
        rule = RecurringRule.objects.get()

        self.post_rule(reverse("rule_edit", args=[rule.pk]), amount="0.00")

        rule.refresh_from_db()
        self.assertEqual(rule.amount, Decimal("999.00"))

    def test_disabled_category_is_rejected_on_create(self):
        rule = self.make_rule(category=self.disabled)
        with self.assertRaises(ValidationError) as caught:
            rule.full_clean()
        self.assertIn("category", caught.exception.message_dict)

        self.post_rule(reverse("rule_create"), category=self.disabled.pk)
        self.assertEqual(RecurringRule.objects.count(), 0)

    def test_disabled_category_is_rejected_on_edit(self):
        self.post_rule(reverse("rule_create"))
        rule = RecurringRule.objects.get()

        self.post_rule(
            reverse("rule_edit", args=[rule.pk]), category=self.disabled.pk
        )

        rule.refresh_from_db()
        self.assertEqual(rule.category, self.subscriptions)

    def test_disabled_categories_are_not_offered_in_the_form(self):
        response = self.client.get(reverse("rule_create"))
        choices = response.context["form"].fields["category"].queryset
        self.assertIn(self.subscriptions, choices)
        self.assertNotIn(self.disabled, choices)

    def test_an_income_category_is_allowed(self):
        """A rule has no type of its own; the generated transaction takes its
        type from the category (SRS Appendix C), so Income is valid here."""
        rule = self.make_rule(category=self.salary)
        rule.full_clean()
        rule.save()
        self.assertEqual(RecurringRule.objects.get().category, self.salary)

    def test_weekly_frequency_is_accepted(self):
        rule = self.make_rule(frequency=RecurringRule.Frequency.WEEKLY)
        rule.full_clean()
        rule.save()
        self.assertEqual(
            RecurringRule.objects.get().frequency, RecurringRule.Frequency.WEEKLY
        )


class RecurringRuleOwnership(RecurringTestData):
    """A user may only reach their own rules (SEC-002, TC-SEC-07)."""

    def setUp(self):
        super().setUp()
        self.rule = self.make_rule()
        self.rule.full_clean()
        self.rule.save()
        self.other = User.objects.create_user(
            email="bob@test.com", password="Str0ng#Pass1", name="Bob"
        )
        self.client.force_login(self.other)

    def test_another_user_cannot_edit_the_rule(self):
        response = self.client.get(reverse("rule_edit", args=[self.rule.pk]))
        self.assertEqual(response.status_code, 404)

    def test_another_user_cannot_deactivate_the_rule(self):
        response = self.client.post(
            reverse("rule_deactivate", args=[self.rule.pk])
        )
        self.assertEqual(response.status_code, 404)
        self.rule.refresh_from_db()
        self.assertTrue(self.rule.is_active)

    def test_another_users_rule_is_not_listed(self):
        response = self.client.get(reverse("rule_list"))
        self.assertNotIn(self.rule, response.context["rules"])


class RecurringRuleListing(RecurringTestData):
    """The list distinguishes active from deactivated rules (FR-019)."""

    def test_list_shows_active_and_inactive_rules(self):
        active = self.make_rule()
        active.full_clean()
        active.save()

        stopped = self.make_rule(category=self.salary)
        stopped.full_clean()
        stopped.save()
        stopped.deactivate()

        response = self.client.get(reverse("rule_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Active")
        self.assertContains(response, "Inactive")
        self.assertEqual(len(response.context["rules"]), 2)

    def test_deactivate_page_asks_for_confirmation_first(self):
        rule = self.make_rule()
        rule.full_clean()
        rule.save()

        response = self.client.get(reverse("rule_deactivate", args=[rule.pk]))

        self.assertEqual(response.status_code, 200)
        rule.refresh_from_db()
        self.assertTrue(rule.is_active)

class TCREC02AutomaticGeneration(RecurringTestData):
    """TC-REC-02 (FR-024): automatic recurring transaction generation."""

    def create_rule(self, **overrides):
        rule = self.make_rule(**overrides)
        rule.full_clean()
        rule.save()
        return rule

    def test_no_transaction_before_due_date(self):
        rule = self.create_rule()

        result = generate_due_transactions(
            run_date=rule.next_run_date - timedelta(days=1)
        )

        self.assertEqual(result["created"], 0)
        self.assertEqual(rule.transactions.count(), 0)

    def test_due_rule_generates_one_recurring_transaction(self):
        rule = self.create_rule()

        result = generate_due_transactions(run_date=rule.next_run_date)

        self.assertEqual(result["created"], 1)

        transaction = rule.transactions.get()
        self.assertEqual(transaction.source, "Recurring")
        self.assertEqual(transaction.amount, Decimal("999.00"))
        self.assertEqual(transaction.type, "Expense")
        self.assertEqual(transaction.date, self.tomorrow)

        rule.refresh_from_db()
        self.assertEqual(
            rule.next_run_date,
            get_next_run_date(self.tomorrow, RecurringRule.Frequency.MONTHLY),
        )

    def test_running_twice_does_not_create_duplicates(self):
        rule = self.create_rule()

        first_result = generate_due_transactions(run_date=self.tomorrow)
        second_result = generate_due_transactions(run_date=self.tomorrow)

        self.assertEqual(first_result["created"], 1)
        self.assertEqual(second_result["created"], 0)
        self.assertEqual(rule.transactions.count(), 1)

    def test_deactivated_rule_does_not_generate_transaction(self):
        rule = self.create_rule()
        rule.deactivate()

        result = generate_due_transactions(run_date=self.tomorrow)

        self.assertEqual(result["created"], 0)
        self.assertEqual(rule.transactions.count(), 0)

    def test_disabled_category_is_skipped_and_flagged(self):
        rule = self.create_rule()

        self.subscriptions.is_active = False
        self.subscriptions.save(update_fields=["is_active"])

        result = generate_due_transactions(run_date=self.tomorrow)

        self.assertEqual(result["created"], 0)
        self.assertEqual(result["skipped"], 1)
        self.assertEqual(rule.transactions.count(), 0)

        rule.refresh_from_db()
        self.assertTrue(rule.category_disabled)

        response = self.client.get(reverse("rule_list"))
        self.assertContains(response, "Category disabled")

    def test_other_active_rules_process_when_one_category_is_disabled(self):
        disabled_rule = self.create_rule()

        active_rule = self.create_rule(
            category=self.salary,
            amount=Decimal("2000.00"),
        )

        self.subscriptions.is_active = False
        self.subscriptions.save(update_fields=["is_active"])

        result = generate_due_transactions(run_date=self.tomorrow)

        self.assertEqual(result["created"], 1)
        self.assertEqual(result["skipped"], 1)
        self.assertEqual(disabled_rule.transactions.count(), 0)
        self.assertEqual(active_rule.transactions.count(), 1)

        generated = active_rule.transactions.get()
        self.assertEqual(generated.type, "Income")
        self.assertEqual(generated.source, "Recurring")

    def test_weekly_rule_advances_by_seven_days(self):
        rule = self.create_rule(
            frequency=RecurringRule.Frequency.WEEKLY
        )

        generate_due_transactions(run_date=self.tomorrow)

        rule.refresh_from_db()
        self.assertEqual(
            rule.next_run_date,
            self.tomorrow + timedelta(days=7),
        )
        self.assertEqual(rule.transactions.count(), 1)
