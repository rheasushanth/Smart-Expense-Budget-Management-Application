from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from budgets.models import Budget
from categories.models import Category
from transactions.models import Transaction

from .queries import (
    InvalidPeriod,
    UnknownChartKind,
    budget_adherence,
    category_report,
    chart_data,
    month_bounds,
    spend_over_time,
)


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


class TCRPT02ChartData(ReportTestData):
    """TC-RPT-02, the figures: every chart comes from the report's data."""

    def test_pie_matches_the_category_report(self):
        self.seed_the_month()

        data = chart_data(self.user, "pie", self.start, self.end)

        self.assertEqual(data["kind"], "pie")
        self.assertEqual(data["labels"], ["Rent", "Food", "Travel"])
        self.assertEqual(data["values"], [3000.00, 1000.00, 1000.00])
        self.assertEqual(data["total"], 5000.00)

    def test_bar_carries_the_same_figures_as_the_pie(self):
        self.seed_the_month()

        pie = chart_data(self.user, "pie", self.start, self.end)
        bar = chart_data(self.user, "bar", self.start, self.end)

        self.assertEqual(bar["labels"], pie["labels"])
        self.assertEqual(bar["values"], pie["values"])

    def test_chart_total_matches_the_report_total(self):
        self.seed_the_month()

        report = category_report(self.user, self.start, self.end)
        for kind in ("pie", "bar", "line"):
            with self.subTest(kind=kind):
                data = chart_data(self.user, kind, self.start, self.end)
                self.assertEqual(
                    Decimal(str(data["total"])).quantize(Decimal("0.01")),
                    report["total"],
                )

    def test_line_plots_one_point_per_day_of_the_period(self):
        self.seed_the_month()

        data = chart_data(self.user, "line", self.start, self.end)

        expected_days = (self.end - self.start).days + 1
        self.assertEqual(len(data["labels"]), expected_days)
        self.assertEqual(len(data["values"]), expected_days)
        self.assertEqual(data["labels"][0], self.start.isoformat())
        # All three seeded transactions fall on the first day of the month.
        self.assertEqual(data["values"][0], 5000.00)

    def test_line_fills_days_without_spending_with_zero(self):
        self.spend(self.food, "1000.00", when=date(2024, 3, 1))
        self.spend(self.rent, "500.00", when=date(2024, 3, 3))

        data = chart_data(
            self.user, "line", date(2024, 3, 1), date(2024, 3, 3)
        )

        self.assertEqual(data["values"], [1000.00, 0.00, 500.00])

    def test_line_can_be_grouped_by_week(self):
        # 4 and 6 March 2024 share a week; 11 March starts the next one.
        self.spend(self.food, "100.00", when=date(2024, 3, 4))
        self.spend(self.food, "200.00", when=date(2024, 3, 6))
        self.spend(self.rent, "700.00", when=date(2024, 3, 11))

        data = chart_data(
            self.user, "line", date(2024, 3, 4), date(2024, 3, 11), group="week"
        )

        self.assertEqual(data["labels"], ["2024-03-04", "2024-03-11"])
        self.assertEqual(data["values"], [300.00, 700.00])

    def test_empty_period_returns_no_points_without_error(self):
        for kind in ("pie", "bar"):
            with self.subTest(kind=kind):
                data = chart_data(self.user, kind, self.start, self.end)
                self.assertEqual(data["labels"], [])
                self.assertEqual(data["total"], 0.00)

    def test_another_users_spend_is_not_charted(self):
        self.seed_the_month()
        other = User.objects.create_user(
            email="bob@test.com", password="Str0ng#Pass1", name="Bob"
        )
        self.spend(self.food, "9999.00", user=other)

        data = chart_data(self.user, "pie", self.start, self.end)
        self.assertEqual(data["total"], 5000.00)

    def test_income_is_not_charted(self):
        self.seed_the_month()
        Transaction.objects.create(
            user=self.user,
            category=self.salary,
            amount=Decimal("20000.00"),
            type=Transaction.TransactionType.INCOME,
            date=self.start,
            note="",
        )

        for kind in ("pie", "bar", "line"):
            with self.subTest(kind=kind):
                data = chart_data(self.user, kind, self.start, self.end)
                self.assertEqual(data["total"], 5000.00)

    def test_unknown_kind_is_rejected(self):
        with self.assertRaises(UnknownChartKind):
            chart_data(self.user, "donut", self.start, self.end)

    def test_start_after_end_is_rejected(self):
        with self.assertRaises(InvalidPeriod):
            chart_data(self.user, "pie", date(2024, 3, 31), date(2024, 3, 1))

    def test_spend_over_time_defaults_an_unknown_grouping_to_days(self):
        self.spend(self.food, "100.00", when=date(2024, 3, 1))

        buckets = spend_over_time(
            self.user, date(2024, 3, 1), date(2024, 3, 2), group="fortnight"
        )

        self.assertEqual(
            buckets, [(date(2024, 3, 1), Decimal("100.00")), (date(2024, 3, 2), Decimal("0.00"))]
        )


class TCRPT02DashboardPage(ReportTestData):
    """TC-RPT-02, the page: the dashboard renders all three canvases."""

    def setUp(self):
        self.client.force_login(self.user)

    def test_dashboard_renders_pie_bar_and_line_canvases(self):
        self.seed_the_month()

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        for kind in ("pie", "bar", "line"):
            with self.subTest(kind=kind):
                self.assertContains(response, f'id="chart-{kind}"')

    def test_dashboard_renders_without_data(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_defaults_to_the_current_month(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.context["start_date"], self.start)
        self.assertEqual(response.context["end_date"], self.end)

    def test_dashboard_period_can_be_chosen(self):
        response = self.client.get(
            reverse("dashboard"),
            {"start_date": "2024-03-01", "end_date": "2024-03-31"},
        )
        self.assertEqual(response.context["start_date"], date(2024, 3, 1))
        self.assertEqual(response.context["group"], "day")

    def test_long_periods_are_grouped_by_week(self):
        response = self.client.get(
            reverse("dashboard"),
            {"start_date": "2024-01-01", "end_date": "2024-12-31"},
        )
        self.assertEqual(response.context["group"], "week")

    def test_dashboard_start_after_end_is_rejected(self):
        response = self.client.get(
            reverse("dashboard"),
            {"start_date": "2024-03-31", "end_date": "2024-03-01"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "must not be after")

    def test_dashboard_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.headers["Location"])


class TCRPT02ChartDataEndpoint(ReportTestData):
    """TC-RPT-02, the endpoint the three charts fetch (SAD v1.1 Section 4.3)."""

    def setUp(self):
        self.client.force_login(self.user)

    def get(self, **params):
        return self.client.get(reverse("chart_data"), params)

    def test_payload_shape_matches_the_report_api(self):
        self.seed_the_month()

        response = self.get(
            kind="pie",
            **{"from": self.start.isoformat(), "to": self.end.isoformat()},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        payload = response.json()
        self.assertEqual(
            sorted(payload.keys()), ["kind", "labels", "total", "values"]
        )
        self.assertEqual(payload["labels"], ["Rent", "Food", "Travel"])
        self.assertEqual(payload["values"], [3000.00, 1000.00, 1000.00])
        self.assertEqual(payload["total"], 5000.00)

    def test_every_kind_is_served(self):
        self.seed_the_month()
        for kind in ("pie", "bar", "line"):
            with self.subTest(kind=kind):
                response = self.get(kind=kind)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["kind"], kind)

    def test_period_defaults_to_the_current_month(self):
        self.seed_the_month()
        self.spend(self.food, "777.00", when=date(2020, 1, 15))

        self.assertEqual(self.get(kind="pie").json()["total"], 5000.00)

    def test_unknown_kind_is_a_400(self):
        response = self.get(kind="donut")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Unknown chart kind", response.json()["error"])

    def test_unknown_grouping_is_a_400(self):
        response = self.get(kind="line", group="fortnight")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Unknown grouping", response.json()["error"])

    def test_start_after_end_is_a_422(self):
        response = self.get(
            kind="pie", **{"from": "2024-03-31", "to": "2024-03-01"}
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("must not be after", response.json()["error"])

    def test_unparseable_date_is_a_422(self):
        response = self.get(kind="pie", **{"from": "last-tuesday"})
        self.assertEqual(response.status_code, 422)
        self.assertIn("yyyy-mm-dd", response.json()["error"])

    def test_another_users_data_is_never_returned(self):
        self.seed_the_month()
        other = User.objects.create_user(
            email="bob@test.com", password="Str0ng#Pass1", name="Bob"
        )
        self.spend(self.food, "9999.00", user=other)

        self.assertEqual(self.get(kind="pie").json()["total"], 5000.00)

    def test_endpoint_requires_login(self):
        self.client.logout()
        response = self.get(kind="pie")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.headers["Location"])
