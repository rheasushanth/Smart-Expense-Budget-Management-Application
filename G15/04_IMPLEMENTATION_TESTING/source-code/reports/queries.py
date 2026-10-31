"""Reporting queries (SAD v1.1, Section 3.4 — Reporting Service).

Kept separate from the views so the aggregation can be unit tested without
HTTP, and so NFR-001's query work has one place to live.
"""

import calendar
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum
from django.db.models.functions import TruncDay, TruncWeek

from budgets.models import Budget
from budgets.services import percentage_used, remaining_for, spend_for
from transactions.models import Transaction

TWO_PLACES = Decimal("0.01")
ONE_PLACE = Decimal("0.1")

CHART_KINDS = ("pie", "bar", "line")
GROUPINGS = ("day", "week")


class UnknownChartKind(ValueError):
    """Raised when a chart kind outside CHART_KINDS is requested (FR-018)."""


class InvalidPeriod(ValueError):
    """Raised when the start date falls after the end date (FR-018)."""


def month_bounds(on_date=None):
    """First and last day of the month containing on_date (default today)."""
    on_date = on_date or date.today()
    last_day = calendar.monthrange(on_date.year, on_date.month)[1]
    return on_date.replace(day=1), on_date.replace(day=last_day)


def category_report(user, start_date, end_date):
    """Expense spend grouped by category for a period (FR-017).

    Returns rows of category name, type, total and percentage of overall
    spend, ordered by total descending, plus the grand total. Income is not
    counted: the report describes spending (SRS Appendix B.7).
    """
    rows = (
        Transaction.objects.filter(
            user=user,
            type=Transaction.TransactionType.EXPENSE,
            date__gte=start_date,
            date__lte=end_date,
        )
        .values("category__name", "category__type")
        .annotate(total=Sum("amount"))
        .order_by("-total", "category__name")
    )

    materialised = [
        {
            "category": row["category__name"],
            "type": row["category__type"],
            "total": (row["total"] or Decimal("0")).quantize(TWO_PLACES),
        }
        for row in rows
    ]

    grand_total = sum(
        (row["total"] for row in materialised), Decimal("0")
    ).quantize(TWO_PLACES)

    for row in materialised:
        if grand_total > 0:
            row["percentage"] = (
                row["total"] / grand_total * 100
            ).quantize(ONE_PLACE)
        else:
            row["percentage"] = Decimal("0.0")

    return {"rows": materialised, "total": grand_total}


def spend_over_time(user, start_date, end_date, group="day"):
    """Expense spend per day or per week across a period (FR-018).

    Buckets with no spending are filled with zero, so the line chart shows a
    continuous trend instead of joining across the gaps.
    """
    if group not in GROUPINGS:
        group = "day"

    truncate = TruncDay if group == "day" else TruncWeek
    rows = (
        Transaction.objects.filter(
            user=user,
            type=Transaction.TransactionType.EXPENSE,
            date__gte=start_date,
            date__lte=end_date,
        )
        .annotate(bucket=truncate("date"))
        .values("bucket")
        .annotate(total=Sum("amount"))
    )
    totals = {
        row["bucket"]: (row["total"] or Decimal("0")).quantize(TWO_PLACES)
        for row in rows
    }

    step = timedelta(days=1 if group == "day" else 7)
    # Weeks are truncated to their Monday, so start the walk on the Monday of
    # the first week to line up with the keys the database returned.
    cursor = start_date
    if group == "week":
        cursor = start_date - timedelta(days=start_date.weekday())

    buckets = []
    while cursor <= end_date:
        buckets.append((cursor, totals.get(cursor, Decimal("0.00"))))
        cursor += step

    return buckets


def chart_data(user, kind, start_date, end_date, group="day"):
    """Labels and values for one chart on the analytics dashboard (FR-018).

    The pie and bar charts are the category totals of category_report(), so
    the dashboard and the report in SAD v1.1 Section 4.5 cannot disagree. The
    line chart is the same spend grouped by day or week instead of category.
    """
    if kind not in CHART_KINDS:
        raise UnknownChartKind(kind)
    if start_date > end_date:
        raise InvalidPeriod((start_date, end_date))

    if kind == "line":
        buckets = spend_over_time(user, start_date, end_date, group)
        labels = [bucket.isoformat() for bucket, _ in buckets]
        values = [total for _, total in buckets]
        total = sum(values, Decimal("0")).quantize(TWO_PLACES)
    else:
        report = category_report(user, start_date, end_date)
        labels = [row["category"] for row in report["rows"]]
        values = [row["total"] for row in report["rows"]]
        total = report["total"]

    return {
        "kind": kind,
        "labels": labels,
        "values": [float(value) for value in values],
        "total": float(total),
    }


def budget_adherence(user, on_date=None):
    """Limit, spent-to-date and remaining for each active budget (FR-017).

    A budget is active when its period has not yet ended — it covers today
    or a later date (SRS Appendix A).
    """
    on_date = on_date or date.today()

    active = [
        budget
        for budget in Budget.objects.filter(user=user).select_related("category")
        if budget.period_end >= on_date
    ]
    active.sort(key=lambda b: (b.category.name, b.start_date))

    report = []
    for budget in active:
        spent = spend_for(budget)
        report.append(
            {
                "budget": budget,
                "category": budget.category.name,
                "period": budget.period,
                "limit": budget.limit_amount,
                "spent": spent,
                "remaining": remaining_for(budget, spent),
                "percentage": percentage_used(budget, spent),
                "over_limit": spent > budget.limit_amount,
            }
        )
    return report
