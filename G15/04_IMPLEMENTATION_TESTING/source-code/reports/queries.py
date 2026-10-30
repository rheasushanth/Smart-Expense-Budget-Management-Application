"""Reporting queries (SAD v1.1, Section 3.4 — Reporting Service).

Kept separate from the views so the aggregation can be unit tested without
HTTP, and so NFR-001's query work has one place to live.
"""

import calendar
from datetime import date
from decimal import Decimal

from django.db.models import Sum

from budgets.models import Budget
from budgets.services import percentage_used, remaining_for, spend_for
from transactions.models import Transaction

TWO_PLACES = Decimal("0.01")
ONE_PLACE = Decimal("0.1")


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
